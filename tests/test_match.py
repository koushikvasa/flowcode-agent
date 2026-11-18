"""Offline tests for the code gates on the matcher's proposals (no LLM call)."""
from datetime import date

from agent.models import Dropped, Evidence, MatchProposal, Opportunity, Signal
from agent.stages.match import check_proposal


def signal(url: str, quote: str) -> Signal:
    return Signal(what_happening="w", channel="tv", evidence=Evidence(url=url, published=date(2026, 11, 1), quote=quote))


SIGNALS = {
    "S1": signal("https://acme.com/a", "Acme's new TV spot airs nationally from November 3."),
    "S2": signal("https://acme.com/a", "The spot features the Acme app and rewards."),
    "S3": signal("https://news.com/b", "Acme is spending heavily on holiday TV."),
}


def proposal(ids: list[str], quote: str = "new TV spot airs nationally") -> MatchProposal:
    return MatchProposal(signal_ids=ids, evidence_quote=quote, title="TV spot", what_happening="w", channel="tv",
                         why_flowcode_fits="f", flowcode_products=["flowcodes"], suggested_play="p", would_measure="m")


def test_a_good_proposal_gets_one_evidence_per_url_and_marks_its_signals_used():
    used: set[str] = set()

    result = check_proposal(proposal(["S1", "S2", "S3"]), SIGNALS, used)

    assert isinstance(result, Opportunity)
    assert [e.url for e in result.evidence] == ["https://acme.com/a", "https://news.com/b"]
    assert used == {"S1", "S2", "S3"}


def test_proposals_are_dropped_for_unknown_signals_reused_signals_or_a_quote_not_in_them():
    assert "unknown signals" in check_proposal(proposal(["S9"]), SIGNALS, set()).reason
    assert "already used" in check_proposal(proposal(["S1"]), SIGNALS, {"S1"}).reason
    made_up = check_proposal(proposal(["S1"], quote="Acme doubled its TV budget"), SIGNALS, set())
    assert isinstance(made_up, Dropped) and "not found" in made_up.reason
