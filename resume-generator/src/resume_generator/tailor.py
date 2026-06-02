"""Claude-drafted per-job YAML from a raw job-description text.

Strategy:
  - profile + experience pool + schema are constant across calls →
    sent once in the system prompt block with cache_control set so we
    don't repay for them on subsequent tailor calls.
  - the JD text goes in the final user turn.
  - Claude returns a YAML document fenced in ```yaml ... ```; we strip
    the fence and return the raw YAML for review (write opt-in).

The output is a *draft* — the user always reviews before committing.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

from . import models


SYSTEM_INSTRUCTIONS = """\
You are an expert technical resume strategist drafting a per-job tailoring config
for a 1-page resume system. The candidate is Shren Patel — AI agent orchestration
engineer. You have:

  1. The candidate's master profile and full bullet pool (every job, every bullet,
     each tagged with `keywords` and `affinities`).
  2. The exact YAML schema you must emit (matches `JobConfig` in models.py).
  3. A raw job-posting text from the user.

Your job:
  - Pick 8–14 bullets total across roles, weighted toward the candidate's
    most-recent and most-relevant work. Always include 3–5 CentrOS bullets if
    relevant; lighter inclusion of older roles (Coursera, D2L, SpringBoard,
    Minted, TransGaming) — at most 1 bullet each, and only if it directly maps
    to a JD requirement.
  - Optionally override 1–3 high-impact CentrOS bullets via `bullet_overrides`
    so the wording mirrors specific JD phrases.
  - Write a 2–3 sentence summary that mirrors the JD's key phrases without
    keyword-stuffing.
  - Extract 8–12 must-have ATS keywords (exact terms the JD uses) plus 4–8
    nice-to-haves.
  - Produce a `skills_emphasis` block (2–4 groups) reordering items so the
    JD-aligned skills lead.

Hard rules:
  - Output ONE valid YAML document wrapped in a ```yaml fenced block. No prose
    outside the fence.
  - All bullet ids you reference MUST exist in the bullet pool you were given.
  - All experience entry ids you reference MUST exist.
  - Do not invent companies, dates, or skills the candidate doesn't have.
"""


def _load_pool_yaml(data_dir: Path) -> str:
    return (data_dir / "experience.yaml").read_text(encoding="utf-8")


def _load_profile_yaml(data_dir: Path) -> str:
    return (data_dir / "profile.yaml").read_text(encoding="utf-8")


def _schema_hint() -> str:
    """Minimal-but-explicit schema example the model can copy."""
    return """\
slug: <kebab-case>
company: <Company>
role: <Role title>
posting_url: <optional URL>
headline: "<Headline tag-line>"
summary: >
  <2-3 sentences mirroring the JD's key phrases>
must_have_keywords:
  - <term>
nice_to_have_keywords:
  - <term>
experience_selection:
  - { job_id: <entry_id>, bullets: [<bullet_id>, <bullet_id>] }
bullet_overrides:
  <bullet_id>: "<rewritten bullet text>"
skills_emphasis:
  - title: "<Group title>"
    items:
      - "<skill line>"
"""


def draft_job_config(
    slug: str, posting_text: str, data_dir: Path, model: str = "claude-opus-4-7"
) -> str:
    """Call Claude. Returns the YAML body (fence stripped) for review."""

    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError(
            "the `anthropic` package is required. Run `uv sync` in resume-generator/."
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var is not set")

    client = anthropic.Anthropic(api_key=api_key)

    # The static context — profile, pool, schema — goes in cacheable blocks.
    profile_yaml = _load_profile_yaml(data_dir)
    pool_yaml = _load_pool_yaml(data_dir)

    system_blocks = [
        {"type": "text", "text": SYSTEM_INSTRUCTIONS},
        {
            "type": "text",
            "text": f"--- PROFILE (profile.yaml) ---\n{profile_yaml}\n",
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"--- BULLET POOL (experience.yaml) ---\n{pool_yaml}\n",
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"--- OUTPUT SCHEMA EXAMPLE ---\n{_schema_hint()}\n",
            "cache_control": {"type": "ephemeral"},
        },
    ]

    user_message = (
        f"Draft a `jobs/{slug}.yaml` for this posting. Use `slug: {slug}`.\n\n"
        f"--- JOB POSTING TEXT ---\n{posting_text}\n"
    )

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
    )

    body = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    return _strip_fence(body)


def _strip_fence(s: str) -> str:
    m = re.search(r"```(?:yaml|yml)?\s*\n(.*?)```", s, re.DOTALL)
    return m.group(1).strip() if m else s.strip()


def validate_draft(draft_yaml: str, data_dir: Path) -> tuple[bool, str]:
    """Parse + cross-check that every referenced id exists in the pool."""
    try:
        parsed = yaml.safe_load(draft_yaml)
        job = models.JobConfig.model_validate(parsed)
    except Exception as e:  # noqa: BLE001
        return False, f"schema error: {e}"

    pool = models.load_experience(data_dir)
    pool_ids = {e.id: {b.id for b in e.bullets} for e in pool.entries}

    for sel in job.experience_selection:
        if sel.job_id not in pool_ids:
            return False, f"unknown experience entry id: {sel.job_id}"
        unknown = [bid for bid in sel.bullets if bid not in pool_ids[sel.job_id]]
        if unknown:
            return False, f"unknown bullet ids in {sel.job_id}: {unknown}"

    return True, "ok"


def write_draft(slug: str, draft_yaml: str, data_dir: Path, overwrite: bool = False) -> Path:
    target = data_dir / "jobs" / f"{slug}.yaml"
    if target.exists() and not overwrite:
        raise FileExistsError(f"{target} exists; pass --overwrite to replace")
    target.write_text(draft_yaml + "\n", encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Cover-letter drafting
# ---------------------------------------------------------------------------


COVER_LETTER_INSTRUCTIONS = """\
You are drafting a 1-page cover letter for Shren Patel — an AI agent
orchestration engineer applying to a specific role. Output ONLY the cover
letter prose, ready to paste into a Greenhouse/Lever/Ashby form or render
into a PDF. No greeting/sign-off (those are added by the LaTeX template).

You have:
  1. The candidate's master profile (profile.yaml).
  2. The full bullet pool (experience.yaml) — every job, every fact, with
     numbers. You may quote these numbers verbatim; do NOT invent new ones.
  3. The target job config (jobs/<slug>.yaml) — summary, must-have keywords,
     and the cover_letter config (tone, paragraphs, must_mention, avoid).
  4. Optionally the raw posting text.

Hard rules:
  - Paragraph count = exactly the `paragraphs` value in cover_letter config.
  - Tone = exactly what `tone` says.
  - Every must_mention term should appear at least once, woven in naturally.
  - Avoid every term in the `avoid` list.
  - 250–350 words total. Tight, technical, no fluff.
  - Lead with a concrete piece of relevant work, not "I'm excited to apply".
  - End with a specific reason this role is the right fit, not a generic
    "I'd love to chat".
  - Use plain prose. No headings, no bullets, no markdown.
  - Numbers from the bullet pool can be quoted directly. Do not invent new ones.
"""


def draft_cover_letter(
    slug: str,
    data_dir: Path,
    posting_text: str | None = None,
    model: str = "claude-opus-4-7",
) -> str:
    """Returns the cover-letter prose (no fence, ready to write to .md)."""

    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError(
            "the `anthropic` package is required. Run `uv sync` in resume-generator/."
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var is not set")

    client = anthropic.Anthropic(api_key=api_key)

    profile_yaml = _load_profile_yaml(data_dir)
    pool_yaml = _load_pool_yaml(data_dir)
    job_yaml = (data_dir / "jobs" / f"{slug}.yaml").read_text(encoding="utf-8")

    system_blocks = [
        {"type": "text", "text": COVER_LETTER_INSTRUCTIONS},
        {
            "type": "text",
            "text": f"--- PROFILE (profile.yaml) ---\n{profile_yaml}\n",
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"--- BULLET POOL (experience.yaml) ---\n{pool_yaml}\n",
            "cache_control": {"type": "ephemeral"},
        },
    ]

    user_parts = [
        f"--- TARGET JOB (jobs/{slug}.yaml) ---\n{job_yaml}\n",
    ]
    if posting_text:
        user_parts.append(f"--- RAW POSTING TEXT ---\n{posting_text}\n")
    user_parts.append(
        "Draft the cover letter prose now. Plain text only, no greeting, no sign-off."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system_blocks,
        messages=[{"role": "user", "content": "\n\n".join(user_parts)}],
    )

    body = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    # Strip any accidental markdown fences.
    body = re.sub(r"^```\w*\n?", "", body.strip())
    body = re.sub(r"\n?```$", "", body).strip()
    return body


def write_cover_letter(slug: str, body: str, data_dir: Path, force: bool = False) -> Path:
    """Write to data/cover-letters/<slug>.md. Refuses to overwrite unless force=True."""
    target_dir = data_dir / "cover-letters"
    target_dir.mkdir(exist_ok=True)
    target = target_dir / f"{slug}.md"
    if target.exists() and not force:
        raise FileExistsError(
            f"{target} exists; pass --force to overwrite (existing draft will be lost)"
        )
    target.write_text(body + "\n", encoding="utf-8")
    return target
