"""YAML → Jinja2 LaTeX → tectonic PDF.

Density knobs are tuned in three preset tiers (normal → compact → ultra). If a
build overflows 1 page, the caller re-invokes `render_and_compile` at the next
tier. After ultra, the build fails with a diagnostic that lists the bullets in
play so the user can trim the per-job YAML.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import models


# ---------------------------------------------------------------------------
# LaTeX escaping
# ---------------------------------------------------------------------------

# Order matters: backslash must be first so its replacement isn't re-escaped.
_TEX_REPLACEMENTS = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def tex_escape(s: object) -> str:
    """Escape arbitrary text for LaTeX text mode.

    Unicode em-dashes, en-dashes, middots, and arrows pass through — we rely on
    inputenc utf-8 plus T1 fontenc + lmodern to render them.
    """
    if s is None:
        return ""
    out = str(s)
    for src, dst in _TEX_REPLACEMENTS:
        out = out.replace(src, dst)
    return out


# ---------------------------------------------------------------------------
# Density tiers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Density:
    name: str
    font_size: float
    margin_h: float
    margin_v: float
    section_spacing_above: float
    section_spacing_below: float
    bullet_spacing: float
    entry_spacing: float


DENSITY_TIERS: list[Density] = [
    Density("normal",  10.0, 0.55, 0.45, 8, 3, 1.2, 4),
    Density("compact", 9.5,  0.50, 0.40, 6, 2, 0.8, 3),
    Density("ultra",   9.0,  0.45, 0.35, 4, 1, 0.4, 2),
]


# ---------------------------------------------------------------------------
# Jinja environment
# ---------------------------------------------------------------------------


def make_jinja_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        block_start_string="((*",
        block_end_string="*))",
        variable_start_string="(((",
        variable_end_string=")))",
        comment_start_string="((#",
        comment_end_string="#))",
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["tex"] = tex_escape
    return env


# ---------------------------------------------------------------------------
# Render context assembly
# ---------------------------------------------------------------------------


@dataclass
class RenderResult:
    pdf_path: Path
    tex_source: str
    density: Density


def _apply_overrides(text: str, overrides: dict[str, str], bullet_id: str) -> str:
    return overrides.get(bullet_id, text)


METRIC_PLACEHOLDER_RE = re.compile(r"<<METRIC:[^>]*>>")


def resolved_bullets(
    job: models.JobConfig, pool: models.ExperiencePool
) -> list[tuple[str, str, str]]:
    """Walk the per-job selection, apply overrides, return [(entry_id, bullet_id, text), …]."""
    out: list[tuple[str, str, str]] = []
    for sel in job.experience_selection:
        entry = pool.find_entry(sel.job_id)
        by_id = {b.id: b for b in entry.bullets}
        for bid in sel.bullets:
            if bid not in by_id:
                raise KeyError(
                    f"bullet '{bid}' not found in entry '{sel.job_id}' "
                    f"(available: {sorted(by_id.keys())})"
                )
            text = _apply_overrides(by_id[bid].text, job.bullet_overrides, bid)
            out.append((sel.job_id, bid, text))
    return out


def check_metric_placeholders(
    job: models.JobConfig, pool: models.ExperiencePool
) -> list[str]:
    """Return bullet IDs whose rendered text still contains <<METRIC: …>>."""
    bad: list[str] = []
    for _, bid, text in resolved_bullets(job, pool):
        if METRIC_PLACEHOLDER_RE.search(text):
            bad.append(bid)
    return bad


def _build_context(
    profile: models.Profile,
    skills: models.SkillsCatalog,
    pool: models.ExperiencePool,
    job: models.JobConfig,
    density: Density,
) -> dict:
    # Experience: walk the per-job selection, look up bullets in the pool,
    # apply overrides.
    experience: list[dict] = []
    for sel in job.experience_selection:
        entry = pool.find_entry(sel.job_id)
        bullets_by_id = {b.id: b for b in entry.bullets}
        chosen: list[str] = []
        for bid in sel.bullets:
            if bid not in bullets_by_id:
                raise KeyError(
                    f"bullet '{bid}' not found in experience entry '{sel.job_id}' "
                    f"(available: {sorted(bullets_by_id.keys())})"
                )
            text = bullets_by_id[bid].text
            text = _apply_overrides(text, job.bullet_overrides, bid)
            chosen.append(text)
        experience.append({
            "role": entry.role,
            "company": entry.company,
            "dates": entry.dates,
            "location": entry.location,
            "stack": entry.stack,
            "bullets": chosen,
        })

    # Skills: per-job emphasis wins; otherwise fall back to master catalog.
    skill_groups = job.skills_emphasis or skills.groups

    return {
        # density
        "font_size":             density.font_size,
        "margin_h":              density.margin_h,
        "margin_v":              density.margin_v,
        "section_spacing_above": density.section_spacing_above,
        "section_spacing_below": density.section_spacing_below,
        "bullet_spacing":        density.bullet_spacing,
        "entry_spacing":         density.entry_spacing,
        # header
        "name":     profile.name,
        "headline": job.headline or profile.default_headline,
        "email":    profile.contact.email,
        "phone":    profile.contact.phone,
        "location": profile.contact.location,
        "links":    [{"label": l.label, "url": l.url} for l in profile.contact.links],
        # body
        "summary":    _strip_trailing_period(job.summary.strip()),
        "experience": experience,
        "skills":     [{"title": g.title, "lines": g.items} for g in skill_groups],
        "education":  [e.model_dump() for e in profile.education],
    }


def _strip_trailing_period(s: str) -> str:
    return s[:-1] if s.endswith(".") else s


# ---------------------------------------------------------------------------
# Tectonic compile
# ---------------------------------------------------------------------------


def _run_tectonic(tex_source: str, work_dir: Path) -> Path:
    tex_path = work_dir / "resume.tex"
    tex_path.write_text(tex_source, encoding="utf-8")

    tectonic = shutil.which("tectonic")
    if not tectonic:
        raise RuntimeError(
            "`tectonic` not found on PATH. Install with `brew install tectonic` "
            "(macOS) or see https://tectonic-typesetting.github.io/"
        )

    proc = subprocess.run(
        [tectonic, "--keep-logs", "--chatter", "minimal", str(tex_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        log_tail = (work_dir / "resume.log").read_text(errors="replace")[-3000:] \
            if (work_dir / "resume.log").exists() else proc.stderr
        raise RuntimeError(
            f"tectonic failed (exit {proc.returncode}).\n"
            f"--- stderr ---\n{proc.stderr}\n"
            f"--- log tail ---\n{log_tail}"
        )
    return work_dir / "resume.pdf"


# ---------------------------------------------------------------------------
# Page count
# ---------------------------------------------------------------------------


def pdf_page_count(pdf_path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("`pdfinfo` not found. Install with `brew install poppler`.")
    proc = subprocess.run(
        [pdfinfo, str(pdf_path)], capture_output=True, text=True, check=True
    )
    m = re.search(r"^Pages:\s+(\d+)", proc.stdout, re.MULTILINE)
    if not m:
        raise RuntimeError(f"could not parse Pages from pdfinfo output:\n{proc.stdout}")
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_once(
    profile: models.Profile,
    skills: models.SkillsCatalog,
    pool: models.ExperiencePool,
    job: models.JobConfig,
    template_dir: Path,
    density: Density,
    work_dir: Path,
) -> RenderResult:
    env = make_jinja_env(template_dir)
    template = env.get_template("resume.tex.j2")
    ctx = _build_context(profile, skills, pool, job, density)
    tex_source = template.render(**ctx)
    pdf_path = _run_tectonic(tex_source, work_dir)
    return RenderResult(pdf_path=pdf_path, tex_source=tex_source, density=density)


def build_resume(
    profile: models.Profile,
    skills: models.SkillsCatalog,
    pool: models.ExperiencePool,
    job: models.JobConfig,
    template_dir: Path,
    output_dir: Path,
    keep_tex: bool = False,
) -> tuple[Path, Density]:
    """Build, retrying at denser tiers if the PDF overflows 1 page.

    Returns (final_pdf_path, density_used).
    Raises RuntimeError if even the densest tier overflows.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    last_error: tuple[Density, int] | None = None

    # Fail fast on unfilled <<METRIC:>> placeholders — before tectonic spin.
    bad = check_metric_placeholders(job, pool)
    if bad:
        raise RuntimeError(
            f"resume '{job.slug}' contains unfilled <<METRIC: …>> placeholders in bullets: "
            + ", ".join(bad)
            + ". Fill the numbers in data/experience.yaml or in this job's bullet_overrides."
        )

    with tempfile.TemporaryDirectory(prefix=f"resume-{job.slug}-") as td:
        work_dir = Path(td)
        for density in DENSITY_TIERS:
            tier_dir = work_dir / density.name
            tier_dir.mkdir()
            result = render_once(profile, skills, pool, job, template_dir, density, tier_dir)
            pages = pdf_page_count(result.pdf_path)
            if pages == 1:
                final_pdf = output_dir / f"resume-{job.slug}.pdf"
                shutil.copy(result.pdf_path, final_pdf)
                if keep_tex:
                    (output_dir / f"resume-{job.slug}.tex").write_text(
                        result.tex_source, encoding="utf-8"
                    )
                return final_pdf, density
            last_error = (density, pages)

        # All tiers failed.
        bullet_counts = ", ".join(
            f"{sel.job_id}={len(sel.bullets)}" for sel in job.experience_selection
        )
        density, pages = last_error  # type: ignore[misc]
        raise RuntimeError(
            f"resume overflows 1 page at densest tier ({density.name}: {pages} pages). "
            f"Trim the per-job YAML — current bullet counts: {bullet_counts}."
        )
