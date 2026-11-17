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


class Opportunity(BaseModel):
    """Output of match(): a Signal mapped to a Flowcode play."""
    title: str
    what_happening: str
    channel: Channel
    evidence: list[Evidence] = Field(min_length=1)  # at least one source, enforced
    flowcode_products: list[str] = Field(min_length=1)
    why_flowcode_fits: str
    suggested_play: str  # written as a pre-call brief a seller could use
    would_measure: str  # what data it would capture or measure
    fit: int = Field(ge=1, le=5)  # LLM-rated against the rubric in flowcode_context.md
    impact: int = Field(ge=1, le=5)


class Verdict(BaseModel):
    """Output of verify(): does the quote actually support the claim?"""
    supported: bool
    reason: str


class Scores(BaseModel):
    """Transparent scoring; every component is 0 to 1."""
    recency: float
    evidence: float
    fit: float
    impact: float
    total: float


class ScoredOpportunity(BaseModel):
    """Output of rank()."""
    opportunity: Opportunity
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
