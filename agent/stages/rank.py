"""rank(): turn verified opportunities into transparent scores. Pure code, no LLM.

score = sum(weight * component), every component 0 to 1, weights in config.py.
"""
import re
from datetime import date
from typing import Literal

from agent import config
from agent.models import Company, Evidence, Opportunity, ScoredOpportunity, Scores, Verdict
from agent.stages.match import context_section
from agent.stages.resolve import domain_of
from agent.stages.verify import CHECK_FIELDS


def _matches(domain: str, site: str) -> bool:
    return domain == site or domain.endswith("." + site)


def tier(url: str, company: Company) -> str:
    """first_party (brand's own site or a press-release wire), major_press, or other."""
    d = domain_of(url)
    if (company.domain and _matches(d, company.domain)) or any(_matches(d, s) for s in config.PRESS_RELEASE_DOMAINS):
        return "first_party"
    if any(_matches(d, s) for s in config.MAJOR_PRESS_DOMAINS):
        return "major_press"
    return "other"


def independent_tiers(evidence: list[Evidence], company: Company) -> dict[str, str]:
    """One entry per domain (two articles on one site are not independent), keeping the best tier."""
    best: dict[str, str] = {}
    for e in evidence:
        d, t = domain_of(e.url), tier(e.url, company)
        if d not in best or config.TIER_WEIGHTS[t] > config.TIER_WEIGHTS[best[d]]:
            best[d] = t
    return best


def recency(newest: date, today: date) -> float:
    """1.0 today, 0.5 at one half-life, 0.25 at two."""
    age = max(0, (today - newest).days)
    return 0.5 ** (age / config.RECENCY_HALF_LIFE_DAYS)


def evidence_score(tiers: dict[str, str]) -> float:
    """Tier weights of independent sites, out of EVIDENCE_FULL_AT. Small sites together count as one:
    they often copy each other, so five blogs must not outweigh the brand's own press release."""
    strong = sum(config.TIER_WEIGHTS[t] for t in tiers.values() if t != "other")
    small = min(config.OTHER_TIER_MAX, sum(config.TIER_WEIGHTS[t] for t in tiers.values() if t == "other"))
    return min(1.0, (strong + small) / config.EVIDENCE_FULL_AT)


def checklist_score(verdict: Verdict, weights: dict[str, float]) -> float:
    """Share of the weight whose question was answered yes."""
    yes = sum(w for field, w in weights.items() if getattr(verdict, field).answer == "yes")
    return yes / sum(weights.values())


def confidence(tiers: dict[str, str], verdict: Verdict, age_days: int) -> Literal["high", "medium", "low"]:
    unknowns = sum(getattr(verdict, f).answer == "unknown" for f in CHECK_FIELDS)
    strong = any(t in ("first_party", "major_press") for t in tiers.values())
    if not strong or unknowns >= config.LOW_MIN_UNKNOWNS or age_days > config.LOW_MIN_AGE_DAYS:
        return "low"  # only blogs and small sites, too many unanswered checks, or old news
    if len(tiers) >= config.HIGH_MIN_SOURCES and unknowns == 0 and age_days <= config.HIGH_MAX_AGE_DAYS:
        return "high"
    return "medium"


def score(opp: Opportunity, verdict: Verdict, company: Company, today: date) -> ScoredOpportunity:
    newest = max(e.published for e in opp.evidence)
    tiers = independent_tiers(opp.evidence, company)
    parts = {
        "recency": recency(newest, today),
        "evidence": evidence_score(tiers),
        "fit": checklist_score(verdict, config.FIT_CHECKS),
        "impact": checklist_score(verdict, config.IMPACT_CHECKS),
    }
    total = sum(config.SCORE_WEIGHTS[k] * v for k, v in parts.items())
    passed = [f for f in CHECK_FIELDS if getattr(verdict, f).answer == "yes"]
    scores = Scores(**{k: round(v, 3) for k, v in parts.items()}, total=round(total, 3), passed=passed)
    return ScoredOpportunity(opportunity=opp, verdict=verdict, scores=scores,
                             confidence=confidence(tiers, verdict, (today - newest).days))


def proof_names() -> list[str]:
    """Names from section A's proof points: "- ESPN College GameDay: 32,000 emails..." -> "ESPN College GameDay"."""
    proof_list = context_section("A").split("### Proof points", 1)[1].split("\n\n")[1]
    return re.findall(r"^- ([^:\n]+):", proof_list, flags=re.M)


def drop_repeated_proofs(ranked: list[ScoredOpportunity], names: list[str]) -> list[ScoredOpportunity]:
    """Each proof point stays only in the highest-ranked play that uses it; later plays lose that sentence.

    The prompt asks for this too, but a seller reading the same result five times stops trusting it.
    """
    used: set[str] = set()
    result = []
    for item in ranked:
        kept = []
        for sentence in re.split(r"(?<=[.!?])\s+", item.opportunity.suggested_play):
            found = {n for n in names if re.search(rf"\b{re.escape(n)}\b", sentence)}
            if found & used:
                continue  # already quoted by a better-ranked play
            used |= found
            kept.append(sentence)
        play = " ".join(kept)
        result.append(item.model_copy(update={"opportunity": item.opportunity.model_copy(update={"suggested_play": play})}))
    return result


def rank(company: Company, verified: list[tuple[Opportunity, Verdict]], today: date | None = None) -> list[ScoredOpportunity]:
    """Score every verified opportunity, best first, with each proof point used once."""
    today = today or date.today()
    scored = [score(opp, verdict, company, today) for opp, verdict in verified]
    ranked = sorted(scored, key=lambda s: s.scores.total, reverse=True)
    return drop_repeated_proofs(ranked, proof_names())
