"""Saved reports: "have we already researched this company?"

Reports are the outputs/<brand>.json files the CLI already writes, so a past run is reused
without any setup. A report matches a query by company name ("taco bell") or domain
("tacobell.com"). Scanning the folder is fine for tens of reports; a hosted version would
swap this folder for cloud file storage behind the same three functions.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent import config
from agent.models import Report
from agent.stages.render import write_outputs
from agent.stages.resolve import domain_of, normalize


def saved_reports(folder: Path | None = None) -> list[Report]:
    """Every saved report, newest first. Files that aren't valid reports are skipped."""
    folder = folder or config.OUTPUTS_DIR
    reports = []
    for path in folder.glob("*.json"):
        try:
            reports.append(Report.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        except (ValueError, OSError):
            continue  # not a report (or unreadable): ignore it rather than break the page
    return sorted(reports, key=lambda r: r.generated_at, reverse=True)


def find(query: str, folder: Path | None = None) -> Report | None:
    """The newest saved report whose company name or domain matches the query, else None."""
    name, domain = normalize(query), domain_of(query.strip())
    for report in saved_reports(folder):
        if name == normalize(report.company.name) or domain == report.company.domain:
            return report
    return None


def is_fresh(report: Report, max_age_days: int = config.REPORT_FRESH_DAYS) -> bool:
    """True if the report is recent enough to show instead of running again."""
    return datetime.now(timezone.utc) - report.generated_at <= timedelta(days=max_age_days)


def save(report: Report) -> None:
    """Save a finished report (same files the CLI writes: <brand>.md and <brand>.json)."""
    write_outputs(report)
