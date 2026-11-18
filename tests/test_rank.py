"""Offline tests for rank.py: proof-point dedupe (and, below, scoring and confidence)."""
from datetime import date

from agent.models import Check, Evidence, Opportunity, ScoredOpportunity, Scores, Verdict
from agent.stages.rank import drop_repeated_proofs, proof_names

TODAY = date(2026, 11, 18)


def make_verdict(answer: str = "yes") -> Verdict:
    check = Check(quote="a quote from the source page", answer=answer)
    return Verdict(reason="ok", supported=True, f1_touchpoint=check, f2_digital_action=check, f3_matches_play=check,
                   i1_scale_stated=check, i2_national=check, i3_live_or_upcoming=check)


def make_opp(play: str = "A play.", evidence: list[Evidence] | None = None) -> Opportunity:
    evidence = evidence or [Evidence(url="https://acme.com/news", published=TODAY, quote="Acme launched a thing.")]
    return Opportunity(signal_ids=["S1"], evidence_quote="Acme launched a thing.", title="t", what_happening="w",
                       channel="tv", why_flowcode_fits="f", flowcode_products=["flowcodes"], suggested_play=play,
                       would_measure="m", evidence=evidence)


def scored(play: str) -> ScoredOpportunity:
    scores = Scores(recency=1, evidence=1, fit=1, impact=1, total=1, passed=[])
    return ScoredOpportunity(opportunity=make_opp(play), verdict=make_verdict(), scores=scores, confidence="high")


def test_proof_names_come_from_the_context_file():
    assert "ESPN College GameDay" in proof_names() and "LOVE CORN" in proof_names()


def test_a_proof_point_is_kept_only_in_the_best_ranked_play():
    names = ["ESPN College GameDay", "CLEAR"]
    plays = ["Your TV spot runs now. As a Flowcode result, ESPN College GameDay got 32,000 emails. Ask this?",
             "Your billboard is live. ESPN College GameDay got 32,000 emails. CLEAR ran 7,000+ codes.",
             "A clear call to action helps. ESPN College GameDay again."]

    result = [s.opportunity.suggested_play for s in drop_repeated_proofs([scored(p) for p in plays], names)]

    assert result[0] == plays[0]  # best play keeps its proof
    assert result[1] == "Your billboard is live. CLEAR ran 7,000+ codes."  # repeat removed, new proof kept
    assert result[2] == "A clear call to action helps."  # lowercase "clear" is not the CLEAR proof point
