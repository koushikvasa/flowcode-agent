"""extract(): read each page with the cheap model and pull out signals, each with an exact quote.

Code, not the LLM, attaches the URL and date, and checks the quote is really on the page.
"""
import asyncio

import anthropic
from pydantic import ValidationError

from agent import config
from agent.llm import LLMError, ask
from agent.models import Company, Dropped, Evidence, ExtractResult, RunStats, Signal, Source

SYSTEM = """You read one web page about {brand} and list what {brand} itself is doing right now.

Look for: marketing campaigns, TV or streaming ads, new products or menu items, packaging,
in-store or retail activity, events and sponsorships, app or loyalty programs, partnerships.

Rules:
- Only things {brand} is doing, launching or running. Skip general news, opinions, history, other brands.
- Only activity in the United States, or global activity that includes the U.S. Skip anything limited
  to other countries (for example a UK store opening or a promotion only in Spain).
- For each finding, first copy the quote: one sentence copied word for word from the page, no edits.
- Then say what is happening in one plain sentence, and pick the closest channel.
- At most 3 findings. If the page has nothing that fits, return an empty list."""

# Characters that differ between a page and a copied quote without changing the words.
_SAME_MEANING = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                               "–": "-", "—": "-", " ": " "})


def _flat(text: str) -> str:
    return " ".join(text.translate(_SAME_MEANING).split()).lower()


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote appears word for word in the text (ignoring quote style, spacing, case)."""
    return bool(quote.strip()) and _flat(quote) in _flat(text)


async def extract_page(company: Company, source: Source, stats: RunStats) -> tuple[list[Signal], list[Dropped]]:
    """One LLM call for one page, then code checks on every finding."""
    prompt = f'<page url="{source.url}" date="{source.published}">\n{source.title}\n\n{source.text}\n</page>'
    result = await ask("extract", SYSTEM.format(brand=company.name), prompt, ExtractResult, stats, max_tokens=4000)

    signals, dropped = [], []
    for item in result.items:
        what = f"{source.url}: {item.what_happening}"
        if not quote_in_text(item.quote, source.text):
            dropped.append(Dropped(stage="extract", what=what, reason="quote not found word for word on the page"))
            continue
        try:
            evidence = Evidence(url=source.url, published=source.published, quote=item.quote)
            signals.append(Signal(what_happening=item.what_happening, channel=item.channel, evidence=evidence))
        except ValidationError as e:  # e.g. missing date or a too-short quote: the types say no
            dropped.append(Dropped(stage="extract", what=what, reason=f"invalid evidence: {e.errors()[0]['msg']}"))
    return signals, dropped


async def extract(company: Company, sources: list[Source], stats: RunStats) -> tuple[list[Signal], list[Dropped]]:
    """Extract from all pages in parallel (capped). A failed page is logged, not fatal."""
    limit = asyncio.Semaphore(config.CONCURRENCY)

    async def run(source: Source) -> tuple[list[Signal], list[Dropped]]:
        async with limit:
            return await extract_page(company, source, stats)

    results = await asyncio.gather(*(run(s) for s in sources), return_exceptions=True)
    signals: list[Signal] = []
    dropped: list[Dropped] = []
    for source, result in zip(sources, results):
        if isinstance(result, (LLMError, anthropic.APIError)):
            dropped.append(Dropped(stage="extract", what=source.url, reason=f"extraction failed: {result}"))
        elif isinstance(result, BaseException):
            raise result  # a bug in our code: fail loudly instead of hiding it
        else:
            signals += result[0]
            dropped += result[1]
    return signals, dropped
