"""run_company(): the whole pipeline for one company. The unit of work: a CLI or a queue worker calls this.

resolve -> research -> extract -> match -> verify -> rank. Every stage's output is saved to
runs/<brand>/<run_id>/ so any run can be inspected or compared with the last one.
"""
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from agent import config
from agent.models import Company, Report, RunStats
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


OnProgress = Callable[[str, str], None]  # (stage, message), e.g. ("research", "39 dated sources")


async def run_company(
    query: str,
    search: SearchProvider | None = None,
    on_progress: OnProgress | None = None,
    company: Company | None = None,
    stats: RunStats | None = None,
) -> Report:
    """Research one company end to end and return the Report (also saved under runs/).

    on_progress is called after each stage (the web app streams these to the page).
    If the caller already resolved the company, pass `company` and the `stats` from that call
    so resolve isn't run (or paid for) twice.
    """
    search = search or ExaProvider()
    stats, started = stats or RunStats(), time.time()
    generated_at = datetime.now(timezone.utc)

    def step(stage: str, message: str) -> None:
        log.info("%s: %s  [$%.3f, %d searches so far]", stage, message, stats.cost_usd, stats.search_calls)
        if on_progress:
            on_progress(stage, message)

    company = company or await resolve(query, search, stats)
    run_dir = config.RUNS_DIR / normalize(company.name).replace(" ", "-") / generated_at.strftime("%Y%m%d-%H%M%S")
    _save(run_dir, "1_company", company)
    customer = ", existing Flowcode customer" if company.is_existing_customer else ""
    step("resolve", f"{company.name} ({company.domain}){customer}")

    sources, dropped = await research(company, search, stats)
    _save(run_dir, "2_sources", sources)
    step("research", f"{len(sources)} dated sources")

    signals, more = await extract(company, sources, stats)
    dropped += more
    _save(run_dir, "3_signals", signals)
    step("extract", f"{len(signals)} signals with exact quotes")

    opportunities, more = await match(company, signals, stats)
    dropped += more
    _save(run_dir, "4_opportunities", opportunities)
    step("match", f"{len(opportunities)} opportunities proposed")

    verified, more = await verify(company, opportunities, sources, stats)
    dropped += more
    _save(run_dir, "5_verified", verified)
    step("verify", f"{len(verified)} passed the judge")

    ranked = rank(company, verified)
    stats.seconds = round(time.time() - started, 1)
    report = Report(company=company, generated_at=generated_at, opportunities=ranked, dropped=dropped, stats=stats)
    _save(run_dir, "6_report", report)
    step("rank", f"{len(ranked)} scored, best first")
    log.info("saved stage outputs to %s", run_dir)
    return report
