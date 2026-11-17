"""render(): the Report as a seller-ready Markdown brief, plus JSON with flat CRM-ready rows."""
import json
from pathlib import Path

from agent import config
from agent.models import Report, ScoredOpportunity
from agent.stages.resolve import domain_of, normalize
from agent.stages.verify import CHECK_FIELDS

CHECK_LABELS = {
    "f1_touchpoint": "F1 names a physical/broadcast touchpoint",
    "f2_digital_action": "F2 names a digital action",
    "f3_matches_play": "F3 matches a Flowcode play",
    "i1_scale_stated": "I1 scale stated",
    "i2_national": "I2 national or multi-market",
    "i3_live_or_upcoming": "I3 running now or upcoming",
}


def crm_row(rank: int, s: ScoredOpportunity, report: Report) -> dict:
    """One flat row per opportunity, stable field names, ready for a CRM import."""
    o, c = s.opportunity, s.scores
    return {
        "company": report.company.name, "domain": report.company.domain,
        "existing_customer": report.company.is_existing_customer, "rank": rank, "title": o.title,
        "channel": o.channel, "products": "; ".join(o.flowcode_products),
        "score_total": c.total, "score_recency": c.recency, "score_evidence": c.evidence,
        "score_fit": c.fit, "score_impact": c.impact, "confidence": s.confidence,
        "checks_passed": "; ".join(c.passed), "newest_source_date": str(max(e.published for e in o.evidence)),
        "source_urls": " | ".join(e.url for e in o.evidence), "what_happening": o.what_happening,
        "why_flowcode_fits": o.why_flowcode_fits, "suggested_play": o.suggested_play,
        "would_measure": o.would_measure, "generated_at": report.generated_at.isoformat(),
    }


def opportunity_md(rank: int, s: ScoredOpportunity) -> str:
    o, c = s.opportunity, s.scores
    sources = "\n".join(f'- {e.published} · [{domain_of(e.url)}]({e.url}): "{e.quote}"' for e in o.evidence)
    failed = [CHECK_LABELS[f] for f in CHECK_FIELDS if f not in c.passed]
    w = config.SCORE_WEIGHTS
    return f"""### {rank}. {o.title}
**Score {c.total:.2f}** · confidence **{s.confidence}** · channel: {o.channel} · products: {", ".join(o.flowcode_products)}

**What's happening:** {o.what_happening}

**Why Flowcode fits:** {o.why_flowcode_fits}

**Suggested play (pre-call brief):** {o.suggested_play}

**What it would measure:** {o.would_measure}

**Sources:**
{sources}

<details><summary>Why this score</summary>

`{c.total:.2f} = {w['recency']}×recency {c.recency:.2f} + {w['evidence']}×evidence {c.evidence:.2f} + {w['fit']}×fit {c.fit:.2f} + {w['impact']}×impact {c.impact:.2f}`

- Passed: {"; ".join(CHECK_LABELS[f] for f in c.passed) or "none"}
- Not passed (no or unknown): {"; ".join(failed) or "none"}
</details>
"""


def dropped_md(report: Report) -> str:
    lines = []
    for stage in ("research", "extract", "match", "verify"):
        items = [d for d in report.dropped if d.stage == stage]
        if items:
            lines.append(f"\n**{stage}** ({len(items)})\n")
            lines += [f"- {d.what[:120]}: {d.reason[:200]}" for d in items]
    return "\n".join(lines) or "Nothing was dropped."


def render_markdown(report: Report) -> str:
    co, st = report.company, report.stats
    top = report.opportunities[: config.TOP_N]
    customer = (f"\n> **Likely existing Flowcode customer.** {co.customer_evidence} Treat these as expansion plays.\n"
                if co.is_existing_customer else "")
    body = "\n".join(opportunity_md(i, s) for i, s in enumerate(top, start=1)) or "No opportunity passed verification."
    return f"""# Flowcode opportunities: {co.name}

{co.domain} · generated {report.generated_at:%Y-%m-%d %H:%M} UTC · {len(report.opportunities)} verified opportunities, top {len(top)} shown
{customer}
Every opportunity below is backed by dated sources with exact quotes, checked by a separate reviewer.
Score = recency, evidence strength, Flowcode fit and impact (weights and checklist in `flowcode_context.md` and `agent/config.py`).

## Top opportunities

{body}
## What we couldn't verify

Items removed along the way, and why. No source, no opportunity.
{dropped_md(report)}

## Run stats

{st.search_calls} searches · {st.input_tokens:,} input / {st.output_tokens:,} output tokens · **${st.cost_usd:.3f}** · {st.seconds:.0f}s
"""


def write_outputs(report: Report) -> tuple[Path, Path]:
    """Write outputs/<brand>.md and outputs/<brand>.json; return their paths."""
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = normalize(report.company.name).replace(" ", "-") or "company"
    md_path, json_path = config.OUTPUTS_DIR / f"{stem}.md", config.OUTPUTS_DIR / f"{stem}.json"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    data = report.model_dump(mode="json")
    data["crm_rows"] = [crm_row(i, s, report) for i, s in enumerate(report.opportunities, start=1)]
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return md_path, json_path
