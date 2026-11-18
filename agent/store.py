"""Saved reports: "have we already researched this company?"

Two places hold reports:
- outputs/<brand>.json, the files the CLI writes. On Vercel these are the committed samples (read-only).
- Vercel Blob, when a Blob store is connected: reports/<domain>/<timestamp>.json, one file per run.

A report matches a query by company name ("taco bell") or domain ("tacobell.com"). Listing and
reading every report is fine for tens of reports; thousands would need an index.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from vercel.blob import sync as blob

from agent import config
from agent.models import Report
from agent.stages.render import write_outputs
from agent.stages.resolve import domain_of, normalize

BLOB_PREFIX = "reports/"


def blob_connected() -> bool:
    """True when Vercel has connected a Blob store to this app (it sets these variables)."""
    return bool(os.environ.get("BLOB_STORE_ID") or os.environ.get("BLOB_READ_WRITE_TOKEN"))


def _parse(raw: bytes | str) -> Report | None:
    try:
        return Report.model_validate(json.loads(raw))
    except ValueError:
        return None  # not a report: ignore it rather than break the page


def _folder_reports(folder: Path) -> list[Report]:
    return [r for path in folder.glob("*.json") if (r := _parse(path.read_text(encoding="utf-8")))]


def _blob_reports() -> list[Report]:
    items = blob.query_blobs(prefix=BLOB_PREFIX)
    return [r for item in items if (r := _parse(blob.get_blob(item.pathname, access="private").body))]


def saved_reports(folder: Path | None = None) -> list[Report]:
    """Every saved report, newest first: the outputs folder, plus Blob when connected."""
    reports = _folder_reports(folder or config.OUTPUTS_DIR)
    if folder is None and blob_connected():
        reports += _blob_reports()
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


def runs_today(folder: Path | None = None) -> int:
    """New runs saved today (UTC): the web app's daily cap counts these."""
    today = datetime.now(timezone.utc).date()
    return sum(r.generated_at.date() == today for r in saved_reports(folder))


def can_save() -> bool:
    """On Vercel the disk is read-only, so a new report needs Blob. Checked before paying for a run."""
    return blob_connected() or not config.ON_VERCEL


def save(report: Report) -> None:
    """Save a finished report: to Blob when connected, else the same files the CLI writes."""
    if not blob_connected():
        write_outputs(report)
        return
    path = f"{BLOB_PREFIX}{report.company.domain}/{report.generated_at:%Y%m%d-%H%M%S}.json"
    body = report.model_dump_json().encode("utf-8")
    blob.put_blob(path, body, access="private", content_type="application/json")
