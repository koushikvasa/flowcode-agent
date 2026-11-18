"""match(): one strong-model call maps all signals to Flowcode opportunities, merging duplicates.

The model proposes; code checks every proposal and attaches the evidence. Scoring happens later.
"""
import re

from agent import config
from agent.llm import ask
from agent.models import Company, Dropped, MatchProposal, MatchResult, Opportunity, RunStats, Signal
from agent.stages.extract import quote_in_text

SYSTEM = """You are a Flowcode sales strategist. You get numbered signals about what {brand} is doing,
each with a quote from a dated source. Turn them into Flowcode opportunities.

<flowcode_product_knowledge>
{products}
</flowcode_product_knowledge>

<how_to_write_the_suggested_play>
{play_guide}
</how_to_write_the_suggested_play>

Steps:
1. Group signals about the same campaign, launch or program. One group = one opportunity; list all its signal IDs.
   The parts of one campaign (a TV spot, a store takeover, a social stunt with the same name, talent or theme)
   are ONE opportunity, not one per touchpoint; its play can cover several touchpoints. A signal about a
   campaign that already has an opportunity goes into that opportunity's signal_ids, never into no_fit.
2. For each group, decide honestly whether a Flowcode product solves something real. If not, put each of
   its signal IDs in no_fit with a short reason. A no_fit is better than a stretched pitch, but no_fit
   means Flowcode does not fit, not "this campaign is already covered" or "small detail of a bigger one".
3. For each opportunity: copy evidence_quote word for word from one of its signals' quotes, then explain
   why Flowcode fits, then pick products, then write the suggested play and what it would measure.

Rules:
- Every signal ID appears exactly once: in one opportunity or in no_fit.
- Products, by ID: flowcodes (QR codes), flowurls (branded short links), flowhubs (landing pages),
  flowid (first-party identity), analytics (analytics and CRM integrations), workspaces_api.
- Use only facts from the signals and the product knowledge. Never invent numbers, dates or names.
{customer_note}"""

EXISTING_CUSTOMER_NOTE = "- {brand} is a likely existing Flowcode customer: frame every play as an expansion."


def context_section(letter: str) -> str:
    """The text of one lettered section (A-D) of flowcode_context.md."""
    text = config.CONTEXT_FILE.read_text(encoding="utf-8")
    found = re.search(rf"^## {letter}\.[^\n]*\n(.*?)(?=^## [A-D]\.|\Z)", text, flags=re.M | re.S)
    if found is None:
        raise ValueError(f"Section {letter} not found in {config.CONTEXT_FILE.name}")
    return found.group(1).strip().rstrip("-").strip()


def signals_prompt(signals: dict[str, Signal]) -> str:
    lines = [
        f'<signal id="{sid}" channel="{s.channel}" date="{s.evidence.published}" url="{s.evidence.url}">\n'
        f'{s.what_happening}\nquote: "{s.evidence.quote}"\n</signal>'
        for sid, s in signals.items()
    ]
    return "<signals>\n" + "\n".join(lines) + "\n</signals>"


def check_proposal(p: MatchProposal, signals: dict[str, Signal], used: set[str]) -> Opportunity | Dropped:
    """Code gates on one proposal; on success, attach evidence (one per URL) from its signals."""
    unknown = [sid for sid in p.signal_ids if sid not in signals]
    if unknown:
        return Dropped(stage="match", what=p.title, reason=f"cites unknown signals {unknown}")
    fresh = [sid for sid in p.signal_ids if sid not in used]  # a signal may back only one opportunity
    if not fresh:
        return Dropped(stage="match", what=p.title, reason="all its signals were already used")
    if not any(quote_in_text(p.evidence_quote, signals[sid].evidence.quote) for sid in fresh):
        return Dropped(stage="match", what=p.title, reason="evidence_quote not found in its signals")
    used.update(fresh)
    evidence = list({signals[sid].evidence.url: signals[sid].evidence for sid in fresh}.values())
    return Opportunity(**p.model_dump(exclude={"signal_ids"}), signal_ids=fresh, evidence=evidence)


def same_campaign(opp: Opportunity, accepted: list[Opportunity]) -> Opportunity | None:
    """The accepted opportunity that already cites more than half of this one's sources, if any.

    Two pitches built on the same articles are almost always one campaign split by touchpoint.
    """
    urls = {e.url for e in opp.evidence}
    for other in accepted:
        if len(urls & {e.url for e in other.evidence}) * 2 > len(urls):
            return other
    return None


async def match(company: Company, signal_list: list[Signal], stats: RunStats) -> tuple[list[Opportunity], list[Dropped]]:
    """Propose opportunities with one call, then keep only the ones that pass the code gates."""
    if not signal_list:
        return [], []
    signals = {f"S{i}": s for i, s in enumerate(signal_list, start=1)}
    note = EXISTING_CUSTOMER_NOTE.format(brand=company.name) if company.is_existing_customer else ""
    system = SYSTEM.format(brand=company.name, products=context_section("A"),
                           play_guide=context_section("D"), customer_note=note)
    result = await ask("match", system, signals_prompt(signals), MatchResult, stats, max_tokens=20000)

    opportunities: list[Opportunity] = []
    dropped: list[Dropped] = []
    used: set[str] = set()
    for proposal in result.opportunities:
        outcome = check_proposal(proposal, signals, used)
        if isinstance(outcome, Opportunity) and (twin := same_campaign(outcome, opportunities)):
            outcome = Dropped(stage="match", what=outcome.title, reason=f"same sources as '{twin.title}': likely the same campaign")
        (dropped if isinstance(outcome, Dropped) else opportunities).append(outcome)
    for nf in result.no_fit:
        if nf.signal_id in signals and nf.signal_id not in used:
            used.add(nf.signal_id)
            dropped.append(Dropped(stage="match", what=signals[nf.signal_id].what_happening, reason=f"no Flowcode fit: {nf.reason}"))
    for sid in signals.keys() - used:  # the model skipped it: log, never lose it silently
        dropped.append(Dropped(stage="match", what=signals[sid].what_happening, reason="not addressed by the match model"))
    return opportunities, dropped
