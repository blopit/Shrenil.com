"""Build-time guardrails.

1. 1-page enforcement is handled in `build.py` (auto-retry then fail).
2. ATS keyword coverage: every `must_have_keywords` term substring-matches
   the pdftotext extraction (case-insensitive).
3. Plaintext contact: email, phone digits, and each link URL appear in the
   extracted text — catches the LaTeX trap where `\href{}{}` would hide the
   email from ATS parsers.
4. Snapshot diff: compare extracted text against a committed snapshot;
   surface unintended changes between builds.
5. Bullet lints (2026 best-practice content guardrail): rendered bullets
   are ≤30 words, contain at least one digit, and ideally open with a strong
   action verb. Length + digit failures fail the build; weak verbs warn.
"""

from __future__ import annotations

import difflib
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import models


# ---------------------------------------------------------------------------
# pdftotext
# ---------------------------------------------------------------------------


def extract_text(pdf_path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("`pdftotext` not found. Install with `brew install poppler`.")
    proc = subprocess.run(
        [pdftotext, "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerifyReport:
    slug: str
    pdf_path: Path
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name=name, passed=passed, detail=detail))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_ats_keywords(
    text: str, must_have: list[str], nice_to_have: list[str] | None = None
) -> tuple[bool, str]:
    lowered = text.lower()

    missing = [kw for kw in must_have if kw.lower() not in lowered]
    nice_missing = [kw for kw in (nice_to_have or []) if kw.lower() not in lowered]

    if missing:
        return False, "missing must-have: " + ", ".join(missing)

    detail = f"all {len(must_have)} must-have terms present"
    if nice_to_have:
        present_nice = len(nice_to_have) - len(nice_missing)
        detail += f" · {present_nice}/{len(nice_to_have)} nice-to-have"
    return True, detail


def check_contact_extractable(text: str, profile: models.Profile) -> tuple[bool, str]:
    """Each contact piece must appear in the plain-text extraction.

    Phone: compare on digit-only normalization so spacing/punctuation in the
    rendered output doesn't matter.
    """
    problems: list[str] = []

    if profile.contact.email.lower() not in text.lower():
        problems.append(f"email '{profile.contact.email}' not in extracted text")

    phone_digits = re.sub(r"\D", "", profile.contact.phone)
    text_digits = re.sub(r"\D", "", text)
    if phone_digits and phone_digits not in text_digits:
        problems.append(f"phone digits '{phone_digits}' not in extracted text")

    for link in profile.contact.links:
        # Compare the rendered label (what `\href{url}{label}` shows in PDF).
        if link.label.lower() not in text.lower():
            problems.append(f"link label '{link.label}' not in extracted text")

    if problems:
        return False, " · ".join(problems)
    return True, "email, phone, all links extractable"


STRONG_VERBS = {
    "added", "architected", "automated", "benchmarked", "brokered", "built",
    "consolidated", "created", "cut", "delivered", "deployed", "designed",
    "developed", "distilled", "dogfooded", "drove", "engineered",
    "established", "fine-tuned", "fixed", "implemented", "improved",
    "increased", "initiated", "instrumented", "integrated", "introduced",
    "launched", "led", "migrated", "open-sourced", "optimized", "owned",
    "pioneered", "productionized", "prototyped", "quantized", "ran",
    "reduced", "refactored", "rolled", "scaled", "shipped", "spearheaded",
    "streamlined",
}

WEAK_VERBS = {
    "assisted", "continued", "early", "handled", "helped", "let",
    "managed", "participated", "responsible", "worked",
}

_WORD_RE = re.compile(r"\b[\w'-]+\b")
_DIGIT_RE = re.compile(r"\d")


def _first_token(text: str) -> str:
    m = _WORD_RE.search(text)
    return m.group(0).lower() if m else ""


def check_bullet_lints(
    job: "models.JobConfig", pool: "models.ExperiencePool"
) -> tuple[bool, str]:
    """≤30 words + ≥1 digit (hard). Strong opening verb (soft / warn-only).

    Returns (passed, multi-line detail). passed=False if any hard rule fails.
    """
    from .build import resolved_bullets, METRIC_PLACEHOLDER_RE

    hard_fails: list[str] = []
    soft_warns: list[str] = []

    for _, bid, text in resolved_bullets(job, pool):
        words = _WORD_RE.findall(text)
        wc = len(words)
        if wc > 30:
            hard_fails.append(f"{bid}: {wc}w (>30)")
        elif wc > 28:
            soft_warns.append(f"{bid}: {wc}w")

        if not _DIGIT_RE.search(text):
            hard_fails.append(f"{bid}: no digit")

        if METRIC_PLACEHOLDER_RE.search(text):
            hard_fails.append(f"{bid}: unfilled <<METRIC:>>")

        first = _first_token(text)
        if first in WEAK_VERBS:
            soft_warns.append(f"{bid}: weak verb '{first}'")
        elif first and first not in STRONG_VERBS:
            soft_warns.append(f"{bid}: '{first}' not in strong-verb list")

    if hard_fails:
        return False, "FAIL — " + "; ".join(hard_fails)

    n = len(list(resolved_bullets(job, pool)))
    detail = f"{n} bullets within length/digit rules"
    if soft_warns:
        detail += f" · warn: {'; '.join(soft_warns)}"
    return True, detail


def check_snapshot(
    extracted_text: str, pdf_path: Path, snapshot_dir: Path, update: bool
) -> tuple[bool, str]:
    snap_txt = snapshot_dir / "resume.txt"
    snap_pdf = snapshot_dir / "resume.pdf"

    if update:
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snap_txt.write_text(extracted_text, encoding="utf-8")
        shutil.copy(pdf_path, snap_pdf)
        return True, f"snapshot updated at {snapshot_dir}"

    if not snap_txt.exists():
        return True, f"no prior snapshot (run with --update to create at {snapshot_dir})"

    prev = snap_txt.read_text(encoding="utf-8")
    if prev == extracted_text:
        return True, "no changes vs snapshot"

    diff = list(difflib.unified_diff(
        prev.splitlines(), extracted_text.splitlines(),
        fromfile="snapshot", tofile="current", lineterm="",
    ))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    # Diff is informational — does not fail the build by default.
    return True, f"changed vs snapshot: +{added} / -{removed} lines (re-run with --update to refresh)"


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------


def verify(
    pdf_path: Path,
    job: models.JobConfig,
    profile: models.Profile,
    snapshot_dir: Path,
    update_snapshot: bool = False,
    pool: "models.ExperiencePool | None" = None,
) -> VerifyReport:
    text = extract_text(pdf_path)
    report = VerifyReport(slug=job.slug, pdf_path=pdf_path)

    # 1-page check (re-confirmed after the build also verifies it).
    from .build import pdf_page_count
    pages = pdf_page_count(pdf_path)
    report.add("1 page", pages == 1, f"{pages} page(s)")

    # ATS coverage
    passed, detail = check_ats_keywords(text, job.must_have_keywords, job.nice_to_have_keywords)
    report.add("ATS keyword coverage", passed, detail)

    # Contact plaintext
    passed, detail = check_contact_extractable(text, profile)
    report.add("contact plaintext", passed, detail)

    # Bullet lints (≤30 words · ≥1 digit · strong verbs)
    if pool is not None:
        passed, detail = check_bullet_lints(job, pool)
        report.add("bullet lints", passed, detail)

    # Snapshot diff
    passed, detail = check_snapshot(text, pdf_path, snapshot_dir, update_snapshot)
    report.add("snapshot diff", passed, detail)

    return report
