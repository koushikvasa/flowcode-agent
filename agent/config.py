"""Every tunable number in one place. Change behavior here, not in the stages."""
from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
CONTEXT_FILE = ROOT / "flowcode_context.md"  # product knowledge, checklist, customers
CACHE_DIR = ROOT / ".cache"  # search results and pages, keyed by hash
RUNS_DIR = ROOT / "runs"  # every stage's output, per brand and run
OUTPUTS_DIR = ROOT / "outputs"  # final <brand>.md and <brand>.json

# --- Models: cheap model for bulk extraction, strong model where judgment matters ---
EXTRACT_MODEL = "claude-haiku-5-5"
MATCH_MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "claude-sonnet-5-5"
# Effort controls how much the model thinks (thinking tokens are billed as output).
EFFORT = {"extract": "low", "match": "medium", "judge": "medium"}

# --- Prices, for the cost line at the end of every run ---
# USD per 1M tokens (input, output). Checked 2026-11-17. Haiku price is for prompts under 100K tokens.
PRICE_PER_MTOK = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}
EXA_COST_PER_SEARCH = 0.007  # measured on a real call, 2026-11-17

# --- Research ---
RESULTS_PER_QUERY = 5
LOOKBACK_DAYS = 365  # only search pages published in the last year
MAX_PAGE_CHARS = 8000  # page text kept per source; quotes are checked against this

# --- Scoring: score = sum(weight * component); every component is 0 to 1 ---
SCORE_WEIGHTS = {"recency": 0.30, "evidence": 0.25, "fit": 0.25, "impact": 0.20}

RECENCY_HALF_LIFE_DAYS = 90  # a 90-day-old source counts half; an assumption to tune

# Checklist weights (questions in flowcode_context.md section B). Equal to start;
# seller feedback could tune them later. fit = share of fit weight answered yes.
FIT_CHECKS = {"f1_touchpoint": 1.0, "f2_digital_action": 1.0, "f3_matches_play": 1.0}
IMPACT_CHECKS = {"i1_scale_stated": 1.0, "i2_national": 1.0, "i3_live_or_upcoming": 1.0}
GATE_CHECK = "f1_touchpoint"  # not a yes = opportunity dropped

# Source tiers: the brand's own words beat press, press beats everything else.
TIER_WEIGHTS = {"first_party": 1.0, "major_press": 0.7, "other": 0.3}
PRESS_RELEASE_DOMAINS = {"businesswire.com", "prnewswire.com", "globenewswire.com"}  # count as first_party
MAJOR_PRESS_DOMAINS = {
    "nytimes.com", "wsj.com", "bloomberg.com", "reuters.com", "apnews.com", "cnbc.com",
    "forbes.com", "adage.com", "adweek.com", "marketingdive.com", "thedrum.com", "digiday.com",
}
EVIDENCE_FULL_AT = 2.0  # sum of tier weights that counts as full evidence (two first-party sources)

# Confidence: rule-based, so a seller can see why.
HIGH_MIN_SOURCES = 2  # plus: one first_party or major_press, no unknowns, newest source under HIGH_MAX_AGE_DAYS
HIGH_MAX_AGE_DAYS = 90
LOW_MIN_UNKNOWNS = 2  # 2+ unknown answers = low
LOW_MIN_AGE_DAYS = 180  # newest source older than this = low

# --- Run ---
TOP_N = 5  # opportunities shown in the report
CONCURRENCY = 8  # parallel network calls
REQUEST_TIMEOUT_S = 30  # web requests
LLM_TIMEOUT_S = 300  # Claude calls; match thinks over all signals at once
REPORT_FRESH_DAYS = 7  # web app: a saved report younger than this is shown instead of re-running
