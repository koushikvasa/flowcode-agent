"""Typed contracts between pipeline stages.

Design rule: the types themselves enforce "no source, no opportunity".
If the LLM returns something that breaks a rule here, Pydantic raises and the
stage drops that item (and logs why) instead of letting it through.
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Channel = Literal[
    "tv", "social", "email", "event", "packaging",
    "retail", "ooh", "sponsorship", "app", "other",
]


class Company(BaseModel):
    """Output of resolve(): who we are researching."""
    name: str
    domain: str
    # Set by resolve() when the brand already appears to be a Flowcode customer.
    is_existing_customer: bool = False
    customer_evidence: str | None = None


class Source(BaseModel):
    """One fetched web page. `text` is what quotes are checked against."""
    url: str
    title: str
    published: date | None = None  # None = undated; undated sources are dropped
    text: str


class Evidence(BaseModel):
    """The proof behind a claim: where, when, and the exact words."""
    url: str = Field(min_length=1)
    published: date  # required, not Optional: no date, no evidence
    quote: str = Field(min_length=10)


class Signal(BaseModel):
    """Output of extract(): one thing the company is doing, with proof."""
    what_happening: str
    channel: Channel
    evidence: Evidence


class ExtractedItem(BaseModel):
    """What the extract LLM returns per finding. Quote first; URL and date are added by code."""
    quote: str  # copied word for word from the page
    what_happening: str
    channel: Channel


class ExtractResult(BaseModel):
    """Everything the extract LLM found on one page (empty if nothing relevant)."""
    items: list[ExtractedItem]


Product = Literal[
    "flowcodes", "flowurls", "flowhubs", "flowid", "analytics", "workspaces_api",
]


class MatchProposal(BaseModel):
    """What the match LLM returns for one opportunity.

    Field order matters: the model writes the evidence and its reasoning
    before it picks products. It does not score; the judge does that.
    """
    signal_ids: list[str] = Field(min_length=1)  # e.g. ["S1", "S4"]; duplicates merged
    evidence_quote: str = Field(min_length=10)  # verbatim from one of those signals
    title: str
    what_happening: str
    channel: Channel
    why_flowcode_fits: str  # the reasoning
    flowcode_products: list[Product] = Field(min_length=1)  # only real products
    suggested_play: str  # pre-call brief, format in flowcode_context.md section D
    would_measure: str  # what data it would capture or measure


class NoFit(BaseModel):
    """A signal the match LLM chose not to turn into an opportunity."""
    signal_id: str
    reason: str


class MatchResult(BaseModel):
    """Full output of the match call: every signal lands in exactly one list."""
    opportunities: list[MatchProposal]
    no_fit: list[NoFit]


class Opportunity(MatchProposal):
    """A proposal plus its evidence, attached by code from the signal_ids."""
    evidence: list[Evidence] = Field(min_length=1)  # at least one source, enforced


Answer = Literal["yes", "no", "unknown"]


class Check(BaseModel):
    """One checklist answer. Quote first, then the answer."""
    quote: str  # exact words from a source; empty if none
    answer: Answer  # unknown counts as no


class Verdict(BaseModel):
    """Output of verify(): the judge's answers (questions in flowcode_context.md section B)."""
    reason: str
    supported: bool  # does the evidence actually support the claim?
    f1_touchpoint: Check  # gate: no yes here, opportunity dropped
    f2_digital_action: Check
    f3_matches_play: Check
    i1_scale_stated: Check
    i2_national: Check
    i3_live_or_upcoming: Check


class Scores(BaseModel):
    """Transparent scoring; every component is 0 to 1."""
    recency: float
    evidence: float
    fit: float
    impact: float
    total: float
    passed: list[str]  # checklist items answered yes, e.g. ["f1_touchpoint", "i2_national"]


class ScoredOpportunity(BaseModel):
    """Output of rank(). Keeps the verdict so the report can show why."""
    opportunity: Opportunity
    verdict: Verdict
    scores: Scores
    confidence: Literal["high", "medium", "low"]


class Dropped(BaseModel):
    """Anything removed along the way, so the report can say what we could not verify."""
    stage: Literal["research", "extract", "match", "verify"]
    what: str
    reason: str


class RunStats(BaseModel):
    """Cost and speed, logged at the end of every run."""
    input_tokens: int = 0
    output_tokens: int = 0
    search_calls: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0


class Report(BaseModel):
    """Final output: saved as JSON and rendered to Markdown."""
    company: Company
    generated_at: datetime
    opportunities: list[ScoredOpportunity]
    dropped: list[Dropped]
    stats: RunStats
