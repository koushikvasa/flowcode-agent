"""Offline tests for rank.py: proof-point dedupe (and, below, scoring and confidence)."""
from datetime import date

import pytest

from agent.models import Check, Company, Evidence, Opportunity, ScoredOpportunity, Scores, Verdict
from agent.stages.rank import confidence, drop_repeated_proofs, evidence_score, proof_names, score

ACME = Company(name="Acme", domain="acme.com")

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


def ev(url: str, published: date = TODAY) -> Evidence:
    return Evidence(url=url, published=published, quote="Acme launched a thing.")


def test_score_is_the_weighted_sum_and_repeat_articles_on_one_site_count_once():
    evidence = [ev("https://acme.com/news/1"), ev("https://www.acme.com/news/2"), ev("https://adweek.com/acme")]

    s = score(make_opp(evidence=evidence), make_verdict("yes"), ACME, TODAY).scores

    # acme.com counts once (first_party 1.0) + adweek.com (major_press 0.7) = 1.7 of the 2.0 needed
    assert s.evidence == 0.85
    assert s.total == pytest.approx(0.30 * 1.0 + 0.25 * 0.85 + 0.25 * 1.0 + 0.20 * 1.0, abs=0.001)  # 0.9625


def test_unknown_answers_count_as_no_in_fit_and_impact():
    s = score(make_opp(), make_verdict("unknown"), ACME, TODAY).scores
    assert s.fit == 0 and s.impact == 0 and s.passed == []


def test_confidence_rules():
    yes, two_unknowns = make_verdict("yes"), make_verdict("yes").model_copy(
        update={"f2_digital_action": Check(quote="q", answer="unknown"), "i1_scale_stated": Check(quote="q", answer="unknown")})
    strong_pair = {"acme.com": "first_party", "adweek.com": "major_press"}

    assert confidence(strong_pair, yes, age_days=10) == "high"
    assert confidence({"acme.com": "first_party"}, yes, age_days=10) == "medium"  # only one source
    assert confidence(strong_pair, yes, age_days=120) == "medium"  # older than 90 days
    assert confidence(strong_pair, two_unknowns, age_days=10) == "low"
    assert confidence({"blog.com": "other", "pointsblog.com": "other"}, yes, age_days=10) == "low"  # blogs only


def test_many_small_sites_count_as_one_and_never_outweigh_the_brand():
    five_blogs = {f"blog{i}.com": "other" for i in range(5)}
    assert evidence_score(five_blogs) == pytest.approx(0.3 / 2.0)  # same as a single blog
    assert evidence_score({"acme.com": "first_party", **five_blogs}) == pytest.approx((1.0 + 0.3) / 2.0)
