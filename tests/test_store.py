"""Offline tests for saved-report lookup (the web app's "already have it" check)."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from agent import config, store
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


class FakeBlob:
    """Stands in for vercel.blob.sync: a dict of pathname -> bytes."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def put_blob(self, pathname, body, *, access, content_type=None):
        self.files[pathname] = body

    def query_blobs(self, *, prefix=None):
        return [SimpleNamespace(pathname=p) for p in self.files if p.startswith(prefix or "")]

    def get_blob(self, pathname, *, access):
        return SimpleNamespace(body=self.files[pathname])


def test_with_blob_connected_reports_are_saved_there_and_found_alongside_the_samples(monkeypatch, tmp_path):
    fake = FakeBlob()
    monkeypatch.setattr(store, "blob", fake)
    monkeypatch.setenv("BLOB_STORE_ID", "store_test")
    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path)
    write(tmp_path, "sample", make_report("Sample Co", "sample.com", days_old=3))

    store.save(make_report("Acme Foods", "acmefoods.com"))

    assert list(fake.files)[0].startswith("reports/acmefoods.com/")
    assert store.find("acmefoods.com").company.name == "Acme Foods"
    assert store.find("Sample Co") is not None  # committed samples still found
    assert store.runs_today() == 1  # only today's run counts toward the daily cap


def test_on_vercel_without_blob_new_runs_are_refused(monkeypatch):
    monkeypatch.delenv("BLOB_STORE_ID", raising=False)
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    monkeypatch.setattr(config, "ON_VERCEL", True)
    assert not store.can_save()
    monkeypatch.setattr(config, "ON_VERCEL", False)
    assert store.can_save()
