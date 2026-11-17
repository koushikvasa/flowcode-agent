"""Web search behind one small interface, so the provider can be swapped (or faked in tests)."""
import os
from datetime import date, timedelta
from typing import Protocol

from exa_py import AsyncExa

from agent import cache, config
from agent.models import RunStats, Source


class SearchProvider(Protocol):
    """Anything with this method can be the search engine."""

    async def search(self, query: str, stats: RunStats) -> list[Source]: ...


def parse_date(value: str | None) -> date | None:
    """'2026-10-01T00:00:00.000Z' -> date(2026, 10, 1). Missing or odd values -> None."""
    try:
        return date.fromisoformat(value[:10]) if value else None
    except ValueError:
        return None


class ExaProvider:
    """Real search via Exa: returns page text and published date in one call."""

    def __init__(self) -> None:
        self._client = AsyncExa(api_key=os.environ["EXA_API_KEY"])

    async def search(self, query: str, stats: RunStats) -> list[Source]:
        since = (date.today() - timedelta(days=config.LOOKBACK_DAYS)).isoformat()
        # The date is part of the key, so a cached search is reused for the rest of the day.
        key = f"{query} | n={config.RESULTS_PER_QUERY} | since={since}"
        rows = cache.get("search", key)
        if rows is None:
            response = await self._client.search(
                query,
                num_results=config.RESULTS_PER_QUERY,
                start_published_date=since,
                contents={"text": {"max_characters": config.MAX_PAGE_CHARS}},
                timeout=config.REQUEST_TIMEOUT_S,
            )
            rows = [
                {"url": r.url, "title": r.title or "", "published": r.published_date, "text": r.text or ""}
                for r in response.results
            ]
            cache.put("search", key, rows)
            stats.search_calls += 1
            cost = getattr(response, "cost_dollars", None)  # Exa reports what it charged
            stats.cost_usd += cost.total if cost else config.EXA_COST_PER_SEARCH
        return [Source(url=r["url"], title=r["title"], published=parse_date(r["published"]), text=r["text"])
                for r in rows]


class FakeProvider:
    """Offline stand-in for tests: returns canned sources per query, costs nothing."""

    def __init__(self, results: dict[str, list[Source]]) -> None:
        self.results = results
        self.queries: list[str] = []  # what was asked, so tests can check it

    async def search(self, query: str, stats: RunStats) -> list[Source]:
        self.queries.append(query)
        return self.results.get(query, [])
