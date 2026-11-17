"""verify(): a separate judge call per opportunity checks the claim and answers the checklist.

The judge sees the full source pages, not the matcher's reasoning. Code then enforces:
a "yes" needs a quote that is really in a source, unsupported claims are dropped,
and no named touchpoint (the gate check) means no opportunity.
"""
import asyncio

import anthropic

from agent import config
from agent.llm import LLMError, ask
from agent.models import Check, Company, Dropped, Opportunity, RunStats, Source, Verdict
from agent.stages.extract import quote_in_text
from agent.stages.match import context_section

CHECK_FIELDS = list(config.FIT_CHECKS) + list(config.IMPACT_CHECKS)

SYSTEM = """You are a strict reviewer. You check one sales opportunity about {brand} against its sources.
Use only the sources. Never assume.

First: does every fact in <claim> (what, when, where, how big) appear in the sources?
The claim describes only what {brand} is doing. Flowcode's proposed play is not part of it and
is not expected to be in the sources. Write the reason, then supported = true or false.

Then answer each checklist question. Field names map to question IDs: f1_touchpoint = F1,
f2_digital_action = F2, f3_matches_play = F3, i1_scale_stated = I1, i2_national = I2,
i3_live_or_upcoming = I3. For each: copy the deciding words from a source as the quote, then answer.

<checklist>
{checklist}
</checklist>

<flowcode_product_knowledge>
{products}
</flowcode_product_knowledge>"""


def enforce_quotes(verdict: Verdict, texts: list[str]) -> Verdict:
    """A 'yes' whose quote is not word for word in a source becomes 'unknown' (which counts as no)."""
    fixes = {}
    for field in CHECK_FIELDS:
        check: Check = getattr(verdict, field)
        if check.answer == "yes" and not any(quote_in_text(check.quote, t) for t in texts):
            fixes[field] = Check(quote=check.quote, answer="unknown")
    return verdict.model_copy(update=fixes)


def claim_prompt(opp: Opportunity, pages: list[Source]) -> str:
    sources = "\n".join(f'<source url="{p.url}" date="{p.published}">\n{p.title}\n\n{p.text}\n</source>'
                        for p in pages)
    # Only the brand facts: the title and play contain our own pitch, which no source will mention.
    return (f"<claim>\n{opp.what_happening}\nChannel: {opp.channel}\n</claim>\n\n"
            f"<sources>\n{sources}\n</sources>")


async def verify_one(company: Company, opp: Opportunity, pages: list[Source], system: str,
                     stats: RunStats) -> tuple[Opportunity, Verdict] | Dropped:
    """Judge one opportunity, then apply the code rules."""
    verdict = await ask("judge", system, claim_prompt(opp, pages), Verdict, stats, max_tokens=8000)
    if not verdict.supported:
        return Dropped(stage="verify", what=opp.title, reason=f"claim not supported by sources: {verdict.reason}")
    verdict = enforce_quotes(verdict, [p.text for p in pages])
    if getattr(verdict, config.GATE_CHECK).answer != "yes":
        return Dropped(stage="verify", what=opp.title, reason="no specific physical or broadcast touchpoint named in the sources")
    return opp, verdict


async def verify(company: Company, opportunities: list[Opportunity], sources: list[Source],
                 stats: RunStats) -> tuple[list[tuple[Opportunity, Verdict]], list[Dropped]]:
    """Judge all opportunities in parallel (capped). A failed judge call drops that opportunity, logged."""
    system = SYSTEM.format(brand=company.name, checklist=context_section("B"), products=context_section("A"))
    by_url = {s.url: s for s in sources}
    limit = asyncio.Semaphore(config.CONCURRENCY)

    async def run(opp: Opportunity) -> tuple[Opportunity, Verdict] | Dropped:
        pages = [by_url[e.url] for e in opp.evidence if e.url in by_url]
        async with limit:
            return await verify_one(company, opp, pages, system, stats)

    results = await asyncio.gather(*(run(o) for o in opportunities), return_exceptions=True)
    kept: list[tuple[Opportunity, Verdict]] = []
    dropped: list[Dropped] = []
    for opp, result in zip(opportunities, results):
        if isinstance(result, (LLMError, anthropic.APIError)):
            dropped.append(Dropped(stage="verify", what=opp.title, reason=f"judge call failed: {result}"))
        elif isinstance(result, BaseException):
            raise result  # a bug in our code: fail loudly
        elif isinstance(result, Dropped):
            dropped.append(result)
        else:
            kept.append(result)
    return kept, dropped
