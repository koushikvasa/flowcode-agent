"""Offline test for run_company's progress callback. Every stage is replaced by a stub: no keys, no cost."""
import asyncio

from agent import config, pipeline
from agent.models import Company, RunStats
from agent.search import FakeProvider

ACME = Company(name="Acme", domain="acme.com")


def stub_stages(monkeypatch, tmp_path, calls: list[str]) -> None:
    async def resolve(query, search, stats):
        calls.append("resolve")
        return ACME

    async def two_lists(*args):
        return [], []

    monkeypatch.setattr(config, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(pipeline, "resolve", resolve)
    for stage in ("research", "extract", "match", "verify"):
        monkeypatch.setattr(pipeline, stage, two_lists)


def test_progress_is_reported_after_each_stage_in_order(monkeypatch, tmp_path):
    calls, events = [], []
    stub_stages(monkeypatch, tmp_path, calls)

    report = asyncio.run(pipeline.run_company("Acme", FakeProvider({}), on_progress=lambda s, m: events.append(s)))

    assert events == ["resolve", "research", "extract", "match", "verify", "rank"]
    assert report.company == ACME and calls == ["resolve"]


def test_an_already_resolved_company_skips_resolve(monkeypatch, tmp_path):
    calls = []
    stub_stages(monkeypatch, tmp_path, calls)

    asyncio.run(pipeline.run_company("Acme", FakeProvider({}), company=ACME, stats=RunStats()))

    assert calls == []
