"""Offline tests for saved-report lookup (the web app's "already have it" check)."""
import json
from datetime import datetime, timedelta, timezone

from agent.models import Company, Report, RunStats
from agent.store import find, is_fresh, saved_reports


def make_report(name: str, domain: str, days_old: int = 0) -> Report:
    when = datetime.now(timezone.utc) - timedelta(days=days_old)
    return Report(company=Company(name=name, domain=domain), generated_at=when,
                  opportunities=[], dropped=[], stats=RunStats())


def write(folder, stem: str, report: Report) -> None:
    (folder / f"{stem}.json").write_text(json.dumps(report.model_dump(mode="json")), encoding="utf-8")


def test_find_matches_by_name_or_domain_and_skips_non_reports(tmp_path):
    write(tmp_path, "acme-foods", make_report("Acme Foods", "acmefoods.com"))
    (tmp_path / "notes.json").write_text('{"not": "a report"}', encoding="utf-8")

    for query in ["Acme Foods", "  acme foods ", "acmefoods.com", "https://www.acmefoods.com/menu"]:
        assert find(query, tmp_path).company.domain == "acmefoods.com", query
    assert find("Other Brand", tmp_path) is None
    assert len(saved_reports(tmp_path)) == 1


def test_saved_reports_are_newest_first_and_freshness_has_a_cutoff(tmp_path):
    write(tmp_path, "old", make_report("Old Co", "old.com", days_old=30))
    write(tmp_path, "new", make_report("New Co", "new.com", days_old=1))

    assert [r.company.name for r in saved_reports(tmp_path)] == ["New Co", "Old Co"]
    assert is_fresh(make_report("X", "x.com", days_old=1), max_age_days=7)
    assert not is_fresh(make_report("X", "x.com", days_old=8), max_age_days=7)
