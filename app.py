"""Web app: one page plus three endpoints around the same run_company() the CLI uses.

Local:  uv run --env-file .env uvicorn app:app --reload   then open http://127.0.0.1:8000

GET /api/reports              companies already analyzed (for the "recent" chips)
GET /api/report?company=X     one saved report, or 404
GET /api/run?company=X        live progress as Server-Sent Events, then the report.
                              A saved report under REPORT_FRESH_DAYS old is returned instead
                              of running again, unless fresh=true.
"""
import asyncio
import json
import logging
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from agent import config, store
from agent.models import Report, RunStats
from agent.pipeline import run_company
from agent.search import ExaProvider
from agent.stages.render import crm_row
from agent.stages.resolve import resolve

HEARTBEAT_S = 15  # send a comment line this often so proxies don't close a quiet stream

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
logging.getLogger("httpx2").setLevel(logging.WARNING)
log = logging.getLogger("agent")
app = FastAPI(title="Flowcode Opportunity Agent")

CompanyQuery = Query(min_length=2, max_length=100, description="company name or website")


def report_json(report: Report, cached: bool) -> dict:
    """The report as the page needs it: full report, CRM rows, and whether it came from a saved run."""
    data = report.model_dump(mode="json")
    data["crm_rows"] = [crm_row(i, s, report) for i, s in enumerate(report.opportunities, start=1)]
    data["cached"] = cached
    data["top_n"] = config.TOP_N  # the page shows this many cards, like the Markdown brief
    return data


def sse(event: str, data: dict) -> str:
    """One Server-Sent Event: the browser's EventSource gets `data` as the named event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/")
def page() -> FileResponse:
    return FileResponse(config.PAGE_FILE)


@app.get("/api/reports")
def list_reports() -> list[dict]:
    """One entry per company (its newest report): every run is kept, but a chip should appear once."""
    newest = {}
    for r in store.saved_reports():  # newest first, so the first one seen per domain wins
        newest.setdefault(r.company.domain, r)
    return [
        {"name": r.company.name, "domain": r.company.domain, "generated_at": r.generated_at.isoformat(),
         "opportunities": len(r.opportunities), "fresh": store.is_fresh(r)}
        for r in newest.values()
    ]


@app.get("/api/report")
def get_report(company: str = CompanyQuery) -> dict:
    report = store.find(company)
    if not report:
        raise HTTPException(404, f"No saved report for {company!r}")
    return report_json(report, cached=True)


def cannot_run() -> str | None:
    """Why a new (paid) run is not allowed right now, or None if it is."""
    if not store.can_save():
        return "This deployment has no report storage connected, so new runs are off. Saved reports still work."
    if store.runs_today() >= config.DAILY_RUN_LIMIT:
        return f"Today's limit of {config.DAILY_RUN_LIMIT} new runs is reached. Saved reports still work; try again tomorrow."
    return None


async def run_events(query: str, fresh: bool) -> AsyncIterator[str]:
    """Run in a background task; stream its progress messages as they arrive, then the report."""
    queue: asyncio.Queue[tuple[str, dict] | None] = asyncio.Queue()

    def saved(lookup: str) -> Report | None:
        report = None if fresh else store.find(lookup)
        return report if report and store.is_fresh(report) else None

    async def work() -> None:
        try:
            if report := saved(query):  # free: matched by the typed name or website
                queue.put_nowait(("report", report_json(report, cached=True)))
                return
            if problem := cannot_run():  # checked before anything is paid for
                queue.put_nowait(("failed", {"message": problem}))
                return
            queue.put_nowait(("progress", {"stage": "resolve", "message": f"Looking up {query}…"}))
            search, stats = ExaProvider(), RunStats()
            company = await resolve(query, search, stats)
            if report := saved(company.domain):  # one search: matched by the resolved domain
                queue.put_nowait(("report", report_json(report, cached=True)))
                return
            report = await run_company(
                query, search, company=company, stats=stats,
                on_progress=lambda stage, message: queue.put_nowait(("progress", {"stage": stage, "message": message})),
            )
            store.save(report)
            queue.put_nowait(("report", report_json(report, cached=False)))
        except Exception:
            log.exception("run failed for %r", query)
            queue.put_nowait(("failed", {"message": "The run failed. Check the server log, then try again."}))
        finally:
            queue.put_nowait(None)  # end of stream

    task = asyncio.create_task(work())  # keeps running (and saves) even if the browser disconnects
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_S)
        except asyncio.TimeoutError:
            yield ": still working\n\n"  # SSE comment line; the browser ignores it
            continue
        if item is None:
            break
        yield sse(*item)
    await task


@app.get("/api/run")
def run(company: str = CompanyQuery, fresh: bool = False) -> StreamingResponse:
    return StreamingResponse(run_events(company.strip(), fresh), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
