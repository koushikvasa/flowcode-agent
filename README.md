# Flowcode Opportunity Agent

Give it a company name or website. It researches what the company is doing **right now**
(campaigns, launches, packaging, events, sponsorships, app and loyalty) and returns a ranked
list of places Flowcode could help. Each opportunity says what's happening, why Flowcode fits,
a suggested play written as a pre-call brief, and **where it was found: URL, date and the exact quote**.

**Core rule: no source, no opportunity.** Anything without a dated, quotable source is dropped,
and the report lists what was dropped and why.

**Sample output (real run, Taco Bell, 2026-11-17):** [outputs/taco-bell.md](outputs/taco-bell.md)
(seller-ready brief) and [outputs/taco-bell.json](outputs/taco-bell.json) (same data plus flat
CRM-ready rows). Cost: **$0.30 and 54 seconds** for one company, from a cold cache.

## Run it

Needs Python 3.11+, [uv](https://docs.astral.sh/uv/), an [Exa](https://exa.ai) key and an Anthropic key.
Put the keys in a `.env` file (git-ignored):

```
EXA_API_KEY=...
ANTHROPIC_API_KEY=...
```

```bash
uv sync                                                   # install
uv run --env-file .env python -m agent "Taco Bell"        # run (a website like tacobell.com also works)
uv run pytest                                             # offline tests, no keys needed
```

Writes `outputs/<brand>.md` and `outputs/<brand>.json`, and saves every stage's output to
`runs/<brand>/<timestamp>/` for inspection.

## How it works

| Stage | What it does | Model |
|---|---|---|
| 1. Resolve | Name to company and domain. Flags likely existing customers from a list in `flowcode_context.md`, then one search. | none |
| 2. Research | 8 parallel web searches (campaign, launch, sponsorship, packaging, TV, loyalty/app, retail, events). Last 12 months only, deduped, undated pages dropped. | Exa |
| 3. Extract | Reads each page and pulls out what the brand is doing, with a word-for-word quote. Code attaches URL and date and **checks the quote is really on the page**. U.S. activity only. | Haiku 5.5 |
| 4. Match | One call sees all signals, merges duplicates about the same campaign, and proposes Flowcode plays, or says "no fit". Code checks every proposal. | Sonnet 5.5 |
| 5. Verify | A separate judge reads the full source pages and checks the claim, then answers 6 yes/no questions. A "yes" needs a quote found in the source. No named physical or broadcast touchpoint means no opportunity. | Sonnet 5.5 |
| 6. Rank | Transparent score in code: `0.30 recency + 0.25 evidence + 0.25 fit + 0.20 impact`. | none |
| 7. Render | Markdown brief (top 5) and JSON. | none |

The Taco Bell run: 39 dated sources, 60 signals, 6 proposed opportunities (17 signals judged
"no Flowcode fit"), **5 verified**. One was dropped by the judge.

**Editable without code:** `flowcode_context.md` holds the product knowledge, the scoring checklist,
the known-customers list (with aliases) and the "suggested play" format. `agent/config.py` holds
every weight, threshold, model and price.

## Key decisions and tradeoffs

- **Sourcing first, enforced by types and code.** An `Evidence` record requires a URL, a date and
  a quote, and every opportunity needs at least one. Quotes are checked word for word against the
  fetched page twice: at extract and at verify. This favors precision over recall: a real
  opportunity with a weak source gets dropped rather than guessed.
- **A checklist judge, not a 1-5 rating.** LLM judges agree far more on yes/no questions than on
  1-5 scales ([CheckEval, EMNLP 2025](https://arxiv.org/abs/2403.18771)), and every score traces back
  to specific answers and quotes. The judge is a separate call from the matcher, as
  [Anthropic's eval guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
  recommends. Fit and impact are the share of "yes" answers. Recency and evidence strength are
  plain math. Each report shows its own formula.
- **Simple, tunable scoring over a black box.** Weights are in config. Recency halves every 90
  days, which is an assumption to tune. Evidence counts independent sites, weighted by tier: brand
  site or press release, then major press, then everything else. Confidence (high, medium, low)
  follows written rules: an opportunity backed only by blogs and small sites is always "low",
  however well it scores.
- **Cheap model for volume, strong model for judgment.** Haiku reads around 40 pages; Sonnet runs
  once to match and once per opportunity to judge.
- **The agent knows nothing about the brand in advance.** Every query contains only the name.
  Everything it learns comes from the searches.
- **U.S. only, by a prompt rule.** It holds well, but it is an instruction, not a code check: in the
  sample run one Northern Ireland item got through extract and was then dropped at match.
- **Known limits:**
  - LLM steps vary a little between runs (the API no longer accepts `temperature`).
  - Undated pages are excluded at search time.
  - About 40 pages per company.
  - Product facts in `flowcode_context.md` are Flowcode's own public claims.
- **Skipped for the time box:** no UI, database or auth. No retries beyond the SDK's own. No
  separate page fetcher (Exa returns page text). No prompt caching or Batch API yet.

## Running it across thousands of companies

The unit of work is one function, `run_company(name) -> Report`. The CLI calls it; a queue worker
would call the same function.

**Cost.** Measured on the Taco Bell run:

| Item | Per company |
|---|---|
| Exa: 10 searches (Exa-reported cost) | $0.07 |
| Extract: Haiku over about 40 pages | ~$0.01 |
| Match: one Sonnet call | ~$0.08 |
| Verify: one Sonnet call per opportunity, reading full pages | ~$0.15 |
| **Total, cold run** | **~$0.30** |

| Accounts | One full refresh | Monthly, refreshing by tier* |
|---|---|---|
| 1,000 | ~$300 | ~$210 |
| 10,000 | ~$3,000 | ~$2,100 |

\*5% of accounts weekly (tier 1), 25% monthly (tier 2), 70% quarterly (tier 3): about 0.7 runs
per account per month. Before any of the savings below.

Ways to bring that down:
- The judge is half the cost because it reads whole pages. Send only the passages around the quotes.
- Cache the shared system prompts (product knowledge and checklist).
- Run non-urgent refreshes through the Batch API, which costs 50% less.
- Only extract and judge sources that are new since the last run (see Freshness).

**Speed.** 54 seconds per company today, with searches and LLM calls already parallel inside a run.
At scale: a queue (SQS, Celery or similar) with N workers, each running `run_company`. A
semaphore and the SDK's backoff respect rate limits. 10,000 companies across 20 workers is about
7.5 hours. Rate limits are the real ceiling, not code.

**Keeping data fresh.**
- Searches are cached per query per day, so reruns the same day are free.
- Every run saves its sources, so the next run can skip pages it has already seen and only
  extract and judge what is new.
- Refresh by account tier.
- Alert when a new opportunity scores above a threshold.

**Checking quality.**
- Built in: the quote checks, the separate judge, the touchpoint gate, and the "what we couldn't
  verify" log.
- At scale, add an eval set: about 20 brands with human-labeled good and bad opportunities.
  Track precision (do sellers agree it's a real play?), source validity (does the quote still
  say that?) and the judge's agreement with humans.
- Re-run the eval on every prompt or model change.
- Sample a few reports each week for human review.

## Turning it into an always-on agent

1. **Watchlist:** customers and prospects, pulled from the CRM, each with a tier and an account owner.
2. **Scheduled runs** by tier, plus event triggers: news, RSS and press-release feeds, the
   brand's own site and social accounts, job posts that mention QR, packaging or loyalty.
3. **Change detection:** keep only sources new since the last run, and keep opportunities that are
   new or have materially changed. Don't re-alert on the same campaign.
4. **Delivery:** push new high-score opportunities to the account owner. Write a Salesforce or
   HubSpot task or opportunity from the `crm_rows` JSON (stable field names, one row per
   opportunity, score components and source URLs), with a Slack message linking the brief.
   Existing customers are flagged as expansion, so sellers aren't pitched accounts they already own.
5. **Feedback loop:** sellers mark an opportunity useful or not useful in Slack or the CRM. Those
   labels become the eval set and re-weight the checklist and score weights over time.

## What I'd do next

- Trim judge input to the relevant passages, add prompt caching, and use the Batch API for
  scheduled runs (estimated 50-70% cost cut).
- Store run history so "new since last run" happens automatically, and track how each
  opportunity changes over time.
- Build the 20-brand eval set and calibrate the judge against human labels.
- Check quote language and country in code, not just in the prompt.
- Add more sources: press-release feeds, the brand's own newsroom, social and job posts.
- Find the likely buyer (role) for each play and connect it to the CRM contact.

## Repo map

```
flowcode_context.md       product knowledge, scoring checklist, known customers, play format (editable)
agent/__main__.py         CLI
agent/pipeline.py         run_company(): runs the stages, saves each stage's output
agent/config.py           models, prices, weights, thresholds
agent/models.py           typed contracts between stages (where "no source, no opportunity" is enforced)
agent/llm.py              one Claude wrapper: structured output, token and cost accounting
agent/search.py           search interface: Exa provider plus a fake provider for tests
agent/cache.py            disk cache, one JSON file per query
agent/stages/             resolve, research, extract, match, verify, rank, render
tests/test_rules.py       offline tests: quote check, recency math, dedupe
outputs/                  sample output (Taco Bell)
```
