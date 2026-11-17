"""run_company(): the whole pipeline for one company. The unit of work: a CLI or a queue worker calls this.

resolve -> research -> extract -> match -> verify -> rank. Every stage's output is saved to
runs/<brand>/<run_id>/ so any run can be inspected or compared with the last one.
"""
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agent import config
from agent.models import Report, RunStats
from agent.search import ExaProvider, SearchProvider
from agent.stages.extract import extract
from agent.stages.match import match
from agent.stages.rank import rank
from agent.stages.research import research
from agent.stages.resolve import normalize, resolve
from agent.stages.verify import verify

log = logging.getLogger("agent")


def _plain(value: Any) -> Any:
    """Pydantic models (also inside lists and tuples) -> plain JSON-ready data."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _save(run_dir: Path, name: str, value: Any) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{name}.json").write_text(json.dumps(_plain(value), indent=1, ensure_ascii=False), encoding="utf-8")


async def run_company(query: str, search: SearchProvider | None = None) -> Report:
    """Research one company end to end and return the Report (also saved under runs/)."""
    search = search or ExaProvider()
    stats, started = RunStats(), time.time()
    generated_at = datetime.now(timezone.utc)

    company = await resolve(query, search, stats)
    run_dir = config.RUNS_DIR / normalize(company.name).replace(" ", "-") / generated_at.strftime("%Y%m%d-%H%M%S")
    _save(run_dir, "1_company", company)
    log.info("resolve: %s (%s), existing customer: %s", company.name, company.domain, company.is_existing_customer)

    sources, dropped = await research(company, search, stats)
    _save(run_dir, "2_sources", sources)
    log.info("research: %d dated sources", len(sources))

    signals, more = await extract(company, sources, stats)
    dropped += more
    _save(run_dir, "3_signals", signals)
    log.info("extract: %d signals", len(signals))

    opportunities, more = await match(company, signals, stats)
    dropped += more
    _save(run_dir, "4_opportunities", opportunities)
    log.info("match: %d opportunities proposed", len(opportunities))

    verified, more = await verify(company, opportunities, sources, stats)
    dropped += more
    _save(run_dir, "5_verified", verified)
    log.info("verify: %d passed the judge", len(verified))

    ranked = rank(company, verified)
    stats.seconds = round(time.time() - started, 1)
    report = Report(company=company, generated_at=generated_at, opportunities=ranked, dropped=dropped, stats=stats)
    _save(run_dir, "6_report", report)
    log.info("rank: done, saved stage outputs to %s", run_dir)
    return report
