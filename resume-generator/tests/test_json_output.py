"""Tests for the ``--json`` flag on the resume-generator CLI.

The flag makes each command emit a single-line JSON payload on stdout
in place of Rich-formatted tables, so external orchestrators (CentrOS
jobs feature) can parse outputs without scraping ANSI text.

Heavy dependencies (Claude API for tailor / cover-letter, tectonic for
build) are mocked via ``monkeypatch`` so the tests run offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from resume_generator import cli as cli_mod


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _last_json_line(stdout: str) -> dict:
    """Return the JSON object from the last non-empty stdout line."""
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout lines\n{stdout!r}"
    return json.loads(lines[-1])


# ---------------------------------------------------------------------------
# tailor --json
# ---------------------------------------------------------------------------


def test_tailor_json_success(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jd_file = tmp_path / "jd.txt"
    jd_file.write_text("Staff AI Engineer. Build inference at scale.")

    monkeypatch.setattr(cli_mod.tailor_mod, "draft_job_config", lambda *a, **kw: "slug: acme\nrole: staff-ai\n")
    monkeypatch.setattr(cli_mod.tailor_mod, "validate_draft", lambda *a, **kw: (True, "valid YAML"))
    written_path = tmp_path / "acme.yaml"
    monkeypatch.setattr(cli_mod.tailor_mod, "write_draft", lambda *a, **kw: written_path)

    result = runner.invoke(
        cli_mod.cli,
        ["tailor", "acme", "--posting", str(jd_file), "--write", "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = _last_json_line(result.output)
    assert payload["ok"] is True
    assert payload["slug"] == "acme"
    assert payload["yaml_path"] == str(written_path)
    assert payload["validation_detail"] == "valid YAML"


def test_tailor_json_validation_failure(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jd_file = tmp_path / "jd.txt"
    jd_file.write_text("JD here")

    monkeypatch.setattr(cli_mod.tailor_mod, "draft_job_config", lambda *a, **kw: "bad yaml")
    monkeypatch.setattr(cli_mod.tailor_mod, "validate_draft", lambda *a, **kw: (False, "missing 'role'"))

    result = runner.invoke(cli_mod.cli, ["tailor", "acme", "--posting", str(jd_file), "--json"])
    assert result.exit_code != 0
    payload = _last_json_line(result.output)
    assert payload["ok"] is False
    assert payload["step"] == "tailor"
    assert "missing 'role'" in payload["error"]


# ---------------------------------------------------------------------------
# build --json
# ---------------------------------------------------------------------------


def test_build_json_success_includes_guardrails(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_pdf = tmp_path / "resume-acme.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n%fake")

    # Skip the real loaders; the command only uses the loaded values to
    # pass into build_resume / verify, both of which are mocked.
    monkeypatch.setattr(cli_mod, "_load_common", lambda: (SimpleNamespace(slug="x"), SimpleNamespace(), SimpleNamespace()))
    monkeypatch.setattr(
        cli_mod.models,
        "load_job",
        lambda data_dir, slug: SimpleNamespace(slug=slug, must_have_keywords=[], nice_to_have_keywords=[]),
    )

    fake_density = SimpleNamespace(name="normal")
    monkeypatch.setattr(cli_mod.build_mod, "build_resume", lambda *a, **kw: (fake_pdf, fake_density))

    # Fake VerifyReport with one check.
    from resume_generator.verify import VerifyReport, CheckResult

    report = VerifyReport(slug="acme", pdf_path=fake_pdf)
    report.checks = [
        CheckResult(name="1 page", passed=True, detail="1 page(s)"),
        CheckResult(name="ATS keyword coverage", passed=True, detail="10/10"),
    ]
    monkeypatch.setattr(cli_mod.verify_mod, "verify", lambda *a, **kw: report)

    result = runner.invoke(cli_mod.cli, ["build", "acme", "--json"])
    assert result.exit_code == 0, result.output
    payload = _last_json_line(result.output)
    assert payload["ok"] is True
    assert payload["slug"] == "acme"
    assert payload["pdf_path"] == str(fake_pdf)
    assert payload["density"] == "normal"
    assert payload["all_passed"] is True
    assert isinstance(payload["guardrails"], list)
    assert payload["guardrails"][0]["name"] == "1 page"
    assert payload["guardrails"][0]["passed"] is True


def test_build_json_reports_guardrail_failure_but_exits_nonzero(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_pdf = tmp_path / "resume-acme.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n%fake")

    monkeypatch.setattr(cli_mod, "_load_common", lambda: (SimpleNamespace(), SimpleNamespace(), SimpleNamespace()))
    monkeypatch.setattr(cli_mod.models, "load_job", lambda data_dir, slug: SimpleNamespace(slug=slug))
    monkeypatch.setattr(cli_mod.build_mod, "build_resume", lambda *a, **kw: (fake_pdf, SimpleNamespace(name="compact")))

    from resume_generator.verify import VerifyReport, CheckResult

    report = VerifyReport(slug="acme", pdf_path=fake_pdf)
    report.checks = [CheckResult(name="ATS keyword coverage", passed=False, detail="2/5 missing")]
    monkeypatch.setattr(cli_mod.verify_mod, "verify", lambda *a, **kw: report)

    result = runner.invoke(cli_mod.cli, ["build", "acme", "--json"])
    assert result.exit_code == 1
    payload = _last_json_line(result.output)
    assert payload["ok"] is False
    assert payload["all_passed"] is False
    assert payload["pdf_path"] == str(fake_pdf)
    assert any(g["name"] == "ATS keyword coverage" and not g["passed"] for g in payload["guardrails"])


# ---------------------------------------------------------------------------
# application --json
# ---------------------------------------------------------------------------


def test_application_json_writes_md_and_returns_path(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_mod, "_load_common", lambda: (SimpleNamespace(), SimpleNamespace(), SimpleNamespace()))
    monkeypatch.setattr(cli_mod.models, "load_application", lambda data_dir: SimpleNamespace())
    monkeypatch.setattr(cli_mod.models, "load_job", lambda data_dir, slug: SimpleNamespace(slug=slug))
    monkeypatch.setattr(cli_mod.application_mod, "check_application", lambda *a, **kw: (True, []))
    monkeypatch.setattr(
        cli_mod.application_mod,
        "render_application_report",
        lambda *a, **kw: "# Application Form\n\nthe form\n",
    )

    out_path = tmp_path / "application-acme.md"
    result = runner.invoke(
        cli_mod.cli, ["application", "acme", "--out", str(out_path), "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = _last_json_line(result.output)
    assert payload["ok"] is True
    assert payload["slug"] == "acme"
    assert payload["md_path"] == str(out_path)
    assert out_path.exists()
    assert "# Application Form" in out_path.read_text()
