"""research(): run targeted searches about the company, keep dated, unique pages with text.

Every query contains only the brand name: everything the agent learns about the
brand comes from what these searches return.
"""
import asyncio
import re
from datetime import date, timedelta
from urllib.parse import urlparse

from agent import config
from agent.models import Company, Dropped, RunStats, Source
from agent.search import SearchProvider

QUERIES = [
    "{brand} new marketing campaign",
    "{brand} new product launch",
    "{brand} sponsorship partnership",
    "{brand} packaging",
    "{brand} TV commercial",
    "{brand} loyalty program app",
    "{brand} retail partnership in-store",
    "{brand} event activation",
]

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")  # 2026-10-01
LONG_DATE = re.compile(r"\b(" + "|".join(MONTHS) + r")[a-z]*\.?\s+(\d{1,2}),?\s+(20\d\d)\b", re.I)  # Oct. 1, 2026


def date_from_text(text: str) -> date | None:
    """Rescue a publish date: the earliest-placed real, non-future date in the top of the page."""
    head = text[:3000]
    found = [(m.start(), int(m[1]), int(m[2]), int(m[3])) for m in ISO_DATE.finditer(head)]
    found += [(m.start(), int(m[3]), MONTHS.index(m[1][:3].lower()) + 1, int(m[2])) for m in LONG_DATE.finditer(head)]
    for _, year, month, day in sorted(found):
        try:
            candidate = date(year, month, day)
        except ValueError:  # e.g. Feb 31
            continue
        if candidate <= date.today():
            return candidate
    return None


def url_key(url: str) -> str:
    """Same page, different spelling -> same key: 'https://www.x.com/a/?utm=1' -> 'x.com/a'."""
    parts = urlparse(url)
    return (parts.netloc.lower().removeprefix("www.") + parts.path.rstrip("/")).lower()


def keep_or_drop(source: Source) -> Source | Dropped:
    """Apply the sourcing rules to one page: it needs text and a recent date."""
    if not source.text.strip():
        return Dropped(stage="research", what=source.url, reason="no page text to check quotes against")
    if source.published is not None:
        return source
    rescued = date_from_text(source.text)
    if rescued is None:
        return Dropped(stage="research", what=source.url, reason="no publish date (search had none, none in page text)")
    if rescued < date.today() - timedelta(days=config.LOOKBACK_DAYS):
        return Dropped(stage="research", what=source.url, reason=f"too old: date in page text is {rescued}")
    return source.model_copy(update={"published": rescued})


async def research(company: Company, search: SearchProvider, stats: RunStats) -> tuple[list[Source], list[Dropped]]:
    """Run all queries in parallel (capped), then dedupe and apply the sourcing rules."""
    limit = asyncio.Semaphore(config.CONCURRENCY)

    async def run(query: str) -> list[Source]:
        async with limit:
            return await search.search(query, stats)

    queries = [q.format(brand=company.name) for q in QUERIES]
    results = await asyncio.gather(*(run(q) for q in queries), return_exceptions=True)

    sources: list[Source] = []
    dropped: list[Dropped] = []
    seen: set[str] = set()
    for query, result in zip(queries, results):
        if isinstance(result, Exception):  # one failed search must not sink the run
            dropped.append(Dropped(stage="research", what=f"search: {query}", reason=f"search failed: {result}"))
            continue
        for source in result:
            if url_key(source.url) in seen:
                continue
            seen.add(url_key(source.url))
            outcome = keep_or_drop(source)
            (dropped if isinstance(outcome, Dropped) else sources).append(outcome)
    return sources, dropped
