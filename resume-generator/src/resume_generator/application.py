"""Application form data renderer + cover letter compile.

`resume application <slug>` renders templates/application.md.j2 to either
stdout or a file. The Markdown sections mirror the standard Greenhouse /
Lever / Ashby form layout so the report is a single-pass copy-paste source.

`resume cover-letter <slug> --build-pdf` compiles the drafted body (from the
job YAML's `application.cover_letter.body`) through templates/cover-letter.tex.j2
into a 1-page PDF, sharing the same fontspec setup as the resume.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import models


# ---------------------------------------------------------------------------
# Jinja env — plain delimiters, not the LaTeX-safe ones build.py uses.
# ---------------------------------------------------------------------------


def _markdown_env(template_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )


def _latex_env(template_dir: Path) -> Environment:
    # Same custom delimiters as build.py — cover-letter.tex.j2 is LaTeX.
    from .build import make_jinja_env
    return make_jinja_env(template_dir)


# ---------------------------------------------------------------------------
# Application Markdown report
# ---------------------------------------------------------------------------


def cover_letter_path(data_dir: Path, slug: str) -> Path:
    return data_dir / "cover-letters" / f"{slug}.md"


def load_cover_letter_body(data_dir: Path, slug: str) -> str | None:
    path = cover_letter_path(data_dir, slug)
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def render_application_report(
    profile: models.Profile,
    application: models.Application,
    job: models.JobConfig,
    template_dir: Path,
    data_dir: Path,
    story_tags: list[str] | None = None,
) -> str:
    overlay = job.application or models.JobApplicationOverlay()
    env = _markdown_env(template_dir)
    template = env.get_template("application.md.j2")
    return template.render(
        profile=profile,
        application=application,
        job=job,
        overlay=overlay,
        story_tags=story_tags or [],
        cover_letter_body=load_cover_letter_body(data_dir, job.slug),
    )


# ---------------------------------------------------------------------------
# Application data check — surfaces "you forgot something" before submitting.
# ---------------------------------------------------------------------------


_RECOMMENDED_TAGS = {
    "incident", "scale", "failure-modes", "ownership", "leadership",
    "cross-team", "ambiguity", "shipping",
}


def check_application(
    application: models.Application, job: models.JobConfig
) -> tuple[bool, list[str]]:
    """Returns (ok, list of warnings). Soft warnings only — never fails build."""
    warns: list[str] = []

    # comp
    c = application.compensation
    if not all([c.base_floor, c.base_target, c.total_target]):
        warns.append("compensation: base_floor/base_target/total_target should all be set")

    # logistics
    if not application.logistics.earliest_start_date:
        warns.append("logistics.earliest_start_date is empty")

    # per-job overlay
    overlay = job.application
    if overlay is None:
        warns.append(f"data/jobs/{job.slug}.yaml has no application: block at all")
    else:
        if not overlay.why_company:
            warns.append("application.why_company missing on this job")
        if not overlay.why_role:
            warns.append("application.why_role missing on this job")
        for q in overlay.custom_questions:
            if q.char_limit and len(q.a) > q.char_limit:
                warns.append(
                    f"custom question '{q.q[:40]}…' answer is {len(q.a)} chars "
                    f"(limit {q.char_limit})"
                )

    # stories coverage
    have_tags = {t.lower() for s in application.stories for t in s.tags}
    missing_tags = _RECOMMENDED_TAGS - have_tags
    if missing_tags:
        warns.append(
            "stories missing tags: " + ", ".join(sorted(missing_tags))
            + " — consider adding a STAR entry"
        )

    return (len(warns) == 0, warns)


# ---------------------------------------------------------------------------
# Cover letter PDF (uses cover-letter.tex.j2 + tectonic)
# ---------------------------------------------------------------------------


def render_cover_letter_pdf(
    profile: models.Profile,
    application: models.Application,
    job: models.JobConfig,
    template_dir: Path,
    output_dir: Path,
    data_dir: Path,
) -> Path:
    body = load_cover_letter_body(data_dir, job.slug)
    if not body:
        raise RuntimeError(
            f"no cover letter body for '{job.slug}' at "
            f"{cover_letter_path(data_dir, job.slug)} — run "
            f"`resume cover-letter {job.slug}` first to draft one."
        )

    env = _latex_env(template_dir)
    template = env.get_template("cover-letter.tex.j2")
    tex_source = template.render(
        name=profile.name,
        email=profile.contact.email,
        phone=profile.contact.phone,
        location=application.logistics.current_location,
        links=[{"label": l.label, "url": l.url} for l in profile.contact.links],
        company=job.company,
        role=job.role,
        body=body,
    )

    tectonic = shutil.which("tectonic")
    if not tectonic:
        raise RuntimeError(
            "`tectonic` not found on PATH. Install with `brew install tectonic`."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"coverletter-{job.slug}-") as td:
        work_dir = Path(td)
        tex_path = work_dir / "cover-letter.tex"
        tex_path.write_text(tex_source, encoding="utf-8")
        proc = subprocess.run(
            [tectonic, "--keep-logs", "--chatter", "minimal", str(tex_path)],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            log_tail = ""
            log_path = work_dir / "cover-letter.log"
            if log_path.exists():
                log_tail = log_path.read_text(errors="replace")[-3000:]
            raise RuntimeError(
                f"tectonic failed for cover letter (exit {proc.returncode}).\n"
                f"--- stderr ---\n{proc.stderr}\n"
                f"--- log tail ---\n{log_tail}"
            )
        pdf_src = work_dir / "cover-letter.pdf"
        final = output_dir / f"cover-letter-{job.slug}.pdf"
        shutil.copy(pdf_src, final)
        return final
