"""Offline tests for the rules that protect "no source, no opportunity". No API keys needed."""
import asyncio
from datetime import date

from agent.models import Company, RunStats, Source
from agent.search import FakeProvider
from agent.stages.extract import quote_in_text
from agent.stages.rank import recency
from agent.stages.research import QUERIES, research

PAGE = "The chain said its new app — launching Nov. 4 — will   reward “every visit.”"


def test_quote_matches_despite_quote_style_dashes_spacing_and_case():
    assert quote_in_text('its new app - launching Nov. 4 - will reward "every visit."', PAGE)
    assert quote_in_text("THE CHAIN SAID", PAGE)


def test_quote_with_a_changed_word_or_empty_is_rejected():
    assert not quote_in_text("its new mobile app", PAGE)
    assert not quote_in_text("   ", PAGE)


def test_recency_halves_every_half_life():
    today = date(2026, 11, 17)
    assert recency(today, today) == 1.0
    assert recency(date(2026, 8, 19), today) == 0.5  # 90 days old
    assert recency(date(2026, 5, 21), today) == 0.25  # 180 days old
    assert recency(date(2026, 12, 1), today) == 1.0  # a future date counts as today


def test_research_keeps_one_copy_of_the_same_page_and_drops_undated():
    page = Source(url="https://acme.com/news/a", title="t", published=date(2026, 10, 1), text="Acme news.")
    same_page = page.model_copy(update={"url": "https://www.acme.com/news/a/?utm_source=x"})
    undated = Source(url="https://blog.com/b", title="t", published=None, text="No date anywhere.")
    first, second = (q.format(brand="Acme") for q in QUERIES[:2])
    fake = FakeProvider({first: [page, undated], second: [same_page]})

    sources, dropped = asyncio.run(research(Company(name="Acme", domain="acme.com"), fake, RunStats()))

    assert [s.url for s in sources] == ["https://acme.com/news/a"]
    assert [d.what for d in dropped] == ["https://blog.com/b"]
