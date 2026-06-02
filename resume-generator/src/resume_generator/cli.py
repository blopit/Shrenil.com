"""Click CLI for the resume generator."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import application as application_mod
from . import build as build_mod
from . import models
from . import tailor as tailor_mod
from . import verify as verify_mod


# ---------------------------------------------------------------------------
# Path resolution — the tool is always run with the project root containing
# `data/` and `templates/`.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]   # resume-generator/
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"
SNAPSHOTS_DIR = ROOT / "snapshots"

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_common() -> tuple[models.Profile, models.SkillsCatalog, models.ExperiencePool]:
    return (
        models.load_profile(DATA_DIR),
        models.load_skills(DATA_DIR),
        models.load_experience(DATA_DIR),
    )


def _print_report(report: verify_mod.VerifyReport, density_name: str | None = None) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Result")
    table.add_column("Detail")
    for c in report.checks:
        mark = "[green]PASS[/green]" if c.passed else "[red]FAIL[/red]"
        table.add_row(c.name, mark, c.detail)
    title = f"[bold]{report.slug}[/bold]  →  {report.pdf_path}"
    if density_name:
        title += f"  (density: [yellow]{density_name}[/yellow])"
    console.rule(title)
    console.print(table)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """Resume generator: per-job tailored 1-page PDFs."""


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@cli.command("list")
def list_jobs() -> None:
    """List all configured target jobs."""
    slugs = models.list_job_slugs(DATA_DIR)
    if not slugs:
        console.print("[yellow]no job configs in data/jobs/[/yellow]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("Slug")
    table.add_column("Company")
    table.add_column("Role")
    for slug in slugs:
        job = models.load_job(DATA_DIR, slug)
        table.add_row(slug, job.company, job.role)
    console.print(table)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


@cli.command("build")
@click.argument("slug", required=False)
@click.option("--all", "build_all", is_flag=True, help="Build every job config")
@click.option("--keep-tex", is_flag=True, help="Write the .tex source next to the PDF")
@click.option("--update-snapshot", is_flag=True, help="Refresh snapshots/<slug>/")
@click.option("--no-verify", is_flag=True, help="Skip post-build guardrails")
def build_cmd(
    slug: str | None,
    build_all: bool,
    keep_tex: bool,
    update_snapshot: bool,
    no_verify: bool,
) -> None:
    """Build resume-<SLUG>.pdf (or --all)."""
    if build_all and slug:
        raise click.UsageError("pass SLUG or --all, not both")
    if not build_all and not slug:
        raise click.UsageError("pass SLUG or --all")

    profile, skills, pool = _load_common()
    slugs = models.list_job_slugs(DATA_DIR) if build_all else [slug]  # type: ignore[list-item]

    failures: list[str] = []
    for s in slugs:
        try:
            job = models.load_job(DATA_DIR, s)
            pdf_path, density = build_mod.build_resume(
                profile, skills, pool, job, TEMPLATES_DIR, OUTPUT_DIR, keep_tex=keep_tex,
            )
            if no_verify:
                console.print(f"[green]✓[/green] {s} → {pdf_path}  ({density.name})")
            else:
                report = verify_mod.verify(
                    pdf_path, job, profile,
                    snapshot_dir=SNAPSHOTS_DIR / s,
                    update_snapshot=update_snapshot,
                    pool=pool,
                )
                _print_report(report, density_name=density.name)
                if not report.passed:
                    failures.append(s)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]✗ {s}: {e}[/red]")
            failures.append(s)

    if failures:
        console.print(f"\n[red]failed: {', '.join(failures)}[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


@cli.command("verify")
@click.argument("slug")
@click.option("--update-snapshot", is_flag=True)
def verify_cmd(slug: str, update_snapshot: bool) -> None:
    """Re-run guardrails on the existing PDF for SLUG."""
    profile, _, pool = _load_common()
    job = models.load_job(DATA_DIR, slug)
    pdf_path = OUTPUT_DIR / f"resume-{slug}.pdf"
    if not pdf_path.exists():
        raise click.ClickException(f"no PDF at {pdf_path} — run `resume build {slug}` first")
    report = verify_mod.verify(
        pdf_path, job, profile,
        snapshot_dir=SNAPSHOTS_DIR / slug, update_snapshot=update_snapshot,
        pool=pool,
    )
    _print_report(report)
    if not report.passed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# tailor
# ---------------------------------------------------------------------------


@cli.command("tailor")
@click.argument("slug")
@click.option(
    "--posting", "-p", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the JD text file. Omit to read from stdin.",
)
@click.option("--write", is_flag=True, help="Write data/jobs/<slug>.yaml")
@click.option("--overwrite", is_flag=True, help="Allow overwriting existing config")
@click.option("--model", default="claude-opus-4-7", show_default=True)
def tailor_cmd(
    slug: str,
    posting: Path | None,
    write: bool,
    overwrite: bool,
    model: str,
) -> None:
    """Draft data/jobs/<SLUG>.yaml from a JD via Claude."""
    if posting:
        text = posting.read_text(encoding="utf-8")
    else:
        console.print("[dim]reading JD from stdin (Ctrl-D to end)...[/dim]")
        text = sys.stdin.read()
    if not text.strip():
        raise click.ClickException("no JD text provided")

    console.print(f"[dim]calling {model} ...[/dim]")
    draft = tailor_mod.draft_job_config(slug, text, DATA_DIR, model=model)

    ok, detail = tailor_mod.validate_draft(draft, DATA_DIR)
    if not ok:
        console.print(f"[red]draft validation failed: {detail}[/red]")
        console.print("\n--- raw draft (for review) ---\n")
        console.print(draft)
        sys.exit(1)

    if write:
        path = tailor_mod.write_draft(slug, draft, DATA_DIR, overwrite=overwrite)
        console.print(f"[green]wrote {path}[/green]  ({detail})")
        console.print(f"next: [bold]resume build {slug}[/bold]")
    else:
        console.print(f"[green]draft valid[/green]  ({detail})\n")
        console.print(draft)
        console.print(f"\n[dim]re-run with --write to save to data/jobs/{slug}.yaml[/dim]")


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------


@cli.command("application")
@click.argument("slug")
@click.option(
    "--out", "-o", type=click.Path(dir_okay=False, path_type=Path),
    help="Write Markdown report to this path instead of stdout.",
)
@click.option(
    "--stories", "tags", multiple=True,
    help="Filter STAR stories by tag. Pass multiple times. Empty = show all.",
)
@click.option("--check/--no-check", default=True, help="Run application data checks.")
def application_cmd(slug: str, out: Path | None, tags: tuple[str, ...], check: bool) -> None:
    """Print a copy-paste-ready Markdown form report for SLUG."""
    profile, _, _ = _load_common()
    application = models.load_application(DATA_DIR)
    job = models.load_job(DATA_DIR, slug)

    if check:
        ok, warns = application_mod.check_application(application, job)
        if warns:
            for w in warns:
                console.print(f"[yellow]⚠ {w}[/yellow]")

    md = application_mod.render_application_report(
        profile, application, job,
        template_dir=TEMPLATES_DIR,
        data_dir=DATA_DIR,
        story_tags=list(tags),
    )
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        console.print(f"[green]wrote {out}[/green]  ({len(md)} chars)")
    else:
        # Bypass rich's markdown rendering — we want raw paste-ready output.
        click.echo(md)


@cli.command("cover-letter")
@click.argument("slug")
@click.option(
    "--posting", "-p", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Optional JD text file to ground the draft. Defaults to job YAML only.",
)
@click.option("--force", is_flag=True, help="Overwrite existing cover letter draft.")
@click.option("--build-pdf", is_flag=True, help="Also compile to output/cover-letter-<slug>.pdf.")
@click.option(
    "--print-only", is_flag=True,
    help="Print draft to stdout, do not write data/cover-letters/<slug>.md.",
)
@click.option("--model", default="claude-opus-4-7", show_default=True)
def cover_letter_cmd(
    slug: str,
    posting: Path | None,
    force: bool,
    build_pdf: bool,
    print_only: bool,
    model: str,
) -> None:
    """Claude-draft a cover letter for SLUG. Writes to data/cover-letters/<slug>.md."""
    # Validate slug exists.
    _ = models.load_job(DATA_DIR, slug)

    existing = application_mod.cover_letter_path(DATA_DIR, slug)
    if existing.exists() and not (force or print_only or build_pdf):
        console.print(
            f"[yellow]cover letter already exists at {existing}[/yellow] — "
            "pass --force to redraft, --build-pdf to compile, or --print-only to preview a new draft."
        )
        sys.exit(0)

    if build_pdf and not (force or print_only):
        # Build path uses the existing draft, no Claude call.
        profile, _, _ = _load_common()
        application = models.load_application(DATA_DIR)
        job = models.load_job(DATA_DIR, slug)
        pdf_path = application_mod.render_cover_letter_pdf(
            profile, application, job,
            template_dir=TEMPLATES_DIR,
            output_dir=OUTPUT_DIR,
            data_dir=DATA_DIR,
        )
        console.print(f"[green]✓ {pdf_path}[/green]")
        return

    posting_text = posting.read_text(encoding="utf-8") if posting else None
    console.print(f"[dim]drafting cover letter via {model} ...[/dim]")
    body = tailor_mod.draft_cover_letter(slug, DATA_DIR, posting_text=posting_text, model=model)

    if print_only:
        click.echo(body)
        return

    path = tailor_mod.write_cover_letter(slug, body, DATA_DIR, force=force)
    console.print(f"[green]wrote {path}[/green]  ({len(body)} chars)")

    if build_pdf:
        profile, _, _ = _load_common()
        application = models.load_application(DATA_DIR)
        job = models.load_job(DATA_DIR, slug)
        pdf_path = application_mod.render_cover_letter_pdf(
            profile, application, job,
            template_dir=TEMPLATES_DIR,
            output_dir=OUTPUT_DIR,
            data_dir=DATA_DIR,
        )
        console.print(f"[green]✓ {pdf_path}[/green]")


@cli.command("snapshot")
@click.argument("slug")
@click.option("--update", is_flag=True, help="Refresh the snapshot")
def snapshot_cmd(slug: str, update: bool) -> None:
    """Compare or refresh snapshots/<SLUG>/."""
    profile, _, _ = _load_common()
    job = models.load_job(DATA_DIR, slug)
    pdf_path = OUTPUT_DIR / f"resume-{slug}.pdf"
    if not pdf_path.exists():
        raise click.ClickException(f"no PDF at {pdf_path} — run `resume build {slug}` first")
    text = verify_mod.extract_text(pdf_path)
    ok, detail = verify_mod.check_snapshot(text, pdf_path, SNAPSHOTS_DIR / slug, update=update)
    console.print(("[green]" if ok else "[red]") + detail + ("[/green]" if ok else "[/red]"))


if __name__ == "__main__":
    cli()
