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

from . import models, verify


SYSTEM_INSTRUCTIONS = """\
You are an expert technical resume strategist drafting a per-job tailoring config
for a 1-page resume system. The candidate is Shren Patel — AI agent orchestration
engineer. You have:

  1. The candidate's master profile and full bullet pool (every job, every bullet,
     each tagged with `keywords` and `affinities`).
  2. The exact YAML schema you must emit (matches `JobConfig` in models.py).
  3. A raw job-posting text from the user.

Your job:
  - Pick 7–8 bullets total across roles, weighted toward the candidate's
    most-recent and most-relevant work. Always include exactly 3 CentrOS
    bullets; lighter inclusion of older roles (Coursera, D2L, SpringBoard,
    Minted, TransGaming) — at most 1 bullet each, and only if it directly maps
    to a JD requirement. The 1-page layout overflows past 8 bullets even at
    its densest tier — every extra role also costs a header line — so 8 is a
    hard ceiling, not a target.
  - Optionally override 1–3 high-impact CentrOS bullets via `bullet_overrides`
    so the wording mirrors specific JD phrases. A rewrite must be at most 30
    words and contain at least one digit: the build lints every rendered
    bullet on exactly those two rules and fails on either, so a rewrite that
    breaks one is discarded before the build and the pooled text is used
    instead.
  - Write a 2–3 sentence summary that mirrors the JD's key phrases without
    keyword-stuffing.
  - Extract 8–12 must-have ATS keywords (exact terms the JD uses) plus 4–8
    nice-to-haves. `must_have_keywords` may contain ONLY terms you have
    actually placed, verbatim, somewhere in the résumé you are composing —
    the `summary`, the `headline`, a `skills_emphasis` item, or a
    `bullet_overrides` rewrite. (A pool bullet you select unchanged counts
    only if its existing text already contains the exact term.) The build
    fails on any must-have the rendered PDF does not contain, so a JD term
    you cannot honestly place goes in `dropped_keywords` instead — that list
    is how the candidate sees what the JD wanted that the résumé lacks.
  - Produce a `skills_emphasis` block (2–4 groups) reordering items so the
    JD-aligned skills lead.

Hard rules:
  - Output ONE valid YAML document wrapped in a ```yaml fenced block. No prose
    outside the fence.
  - All bullet ids you reference MUST exist in the bullet pool you were given.
  - All experience entry ids you reference MUST exist.
  - Never more than 8 bullets total across `experience_selection`.
  - Every `bullet_overrides` rewrite is at most 30 words and contains at
    least one digit.
  - Every `must_have_keywords` term appears verbatim in the summary, headline,
    a skills_emphasis item, or a bullet_overrides rewrite. Terms you could not
    place go in `dropped_keywords`, never in `must_have_keywords`.
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
  - <term placed verbatim in summary / headline / a skills item / an override>
dropped_keywords:
  - <JD term you could not honestly place — never also listed above>
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
    # Parsed once here, before the call, so a malformed pool fails fast and
    # the post-draft keyword prune has the bullet texts to check against.
    pool = models.load_experience(data_dir)

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
    # Order matters: the lint runs before the prune so the prune only counts
    # override text that will survive to the build.
    return _prune_draft(_lint_overrides_draft(_cap_draft(_strip_fence(body))), pool)


def _strip_fence(s: str) -> str:
    m = re.search(r"```(?:yaml|yml)?\s*\n(.*?)```", s, re.DOTALL)
    return m.group(1).strip() if m else s.strip()


# The 1-page layout overflows past this many bullets even at the densest
# density tier (`build` refuses with "resume overflows 1 page"). Measured on
# the 2026-09-10 live run: every 9-bullet package spread over 6–7 roles
# overflowed (each role costs a header line on top of its bullets); every
# 8-bullet package over <=6 roles fit. The prompt asks for 7–8; this is the
# deterministic ceiling if the model overshoots.
MAX_TOTAL_BULLETS = 8


def cap_bullet_budget(
    selection: list[models.ExperienceSelection], limit: int = MAX_TOTAL_BULLETS
) -> list[models.ExperienceSelection]:
    """Drop bullets from the END of the selection (oldest roles first) until
    the total is <= ``limit``. The first entry (CentrOS) always keeps >= 1.
    ``bullet_overrides`` is left alone — build.py ignores overrides whose
    bullet is not selected. Entries emptied by the cap are removed."""
    kept = [list(s.bullets) for s in selection]
    total = sum(len(b) for b in kept)
    i = len(kept) - 1
    while total > limit and i >= 0:
        if kept[i] and (i > 0 or len(kept[i]) > 1):
            kept[i].pop()
            total -= 1
        else:
            i -= 1
    return [
        s.model_copy(update={"bullets": b})
        for s, b in zip(selection, kept)
        if b or not s.bullets
    ]


def _cap_draft(draft_yaml: str) -> str:
    """Enforce MAX_TOTAL_BULLETS on the model's draft. Re-serialises only when
    the cap bites; anything malformed passes through untouched so that
    ``validate_draft`` is the one to report it."""
    try:
        parsed = yaml.safe_load(draft_yaml)
        job = models.JobConfig.model_validate(parsed)
    except Exception:  # noqa: BLE001
        return draft_yaml
    if sum(len(s.bullets) for s in job.experience_selection) <= MAX_TOTAL_BULLETS:
        return draft_yaml
    capped = cap_bullet_budget(job.experience_selection)
    parsed["experience_selection"] = [s.model_dump() for s in capped]
    return yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True, width=100).strip()


def override_lint_failures(text: str) -> list[str]:
    """The hard bullet-lint rules ``text`` breaks, in the build's own wording
    (``"31w (>30)"``, ``"no digit"``); empty when it passes both.

    Mirrors the word-count and digit rules of ``verify.check_bullet_lints``
    — the same ``verify._WORD_RE`` / ``verify._DIGIT_RE`` are imported, not
    re-typed, and the thresholds are the same literals — so the tailor cannot
    drift from what the build enforces. (That check's third hard rule, an
    unfilled ``<<METRIC:>>`` placeholder, is deliberately not mirrored here:
    the pool tolerates placeholders by design and the build refuses them by
    name before it typesets anything.)"""
    failures: list[str] = []
    wc = len(verify._WORD_RE.findall(text))
    if wc > 30:
        failures.append(f"{wc}w (>30)")
    if not verify._DIGIT_RE.search(text):
        failures.append("no digit")
    return failures


def enforce_override_lints(draft: dict) -> dict:
    """Remove every ``bullet_overrides`` rewrite that would fail the build's
    hard bullet lints (``override_lint_failures``); the bullet then renders
    from its pooled text, which the build lints anyway. Removed ids are
    appended to ``dropped_overrides`` (after any already listed, order
    preserved, de-duplicated) so the discard is visible, not silent. Returns
    a new dict with ``dropped_overrides`` placed right after
    ``bullet_overrides``; the input is not mutated. Runs BEFORE the keyword
    prune so the prune counts only text that will actually be rendered."""
    overrides = draft.get("bullet_overrides") or {}
    failing = [
        bid for bid, text in overrides.items()
        if isinstance(text, str) and override_lint_failures(text)
    ]
    if not failing:
        return dict(draft)

    dropped: list[str] = []
    for bid in list(draft.get("dropped_overrides") or []) + failing:
        if bid not in dropped:
            dropped.append(bid)
    kept = {bid: text for bid, text in overrides.items() if bid not in failing}

    out: dict = {}
    for key, val in draft.items():
        if key == "dropped_overrides":
            continue
        out[key] = kept if key == "bullet_overrides" else val
        if key == "bullet_overrides":
            out["dropped_overrides"] = dropped
    return out


def _lint_overrides_draft(draft_yaml: str) -> str:
    """Enforce the build's bullet lints on the model's (already capped)
    ``bullet_overrides``. Same discipline as ``_cap_draft``: re-serialises
    only when an override is dropped; anything malformed passes through
    untouched so that ``validate_draft`` is the one to report it."""
    try:
        parsed = yaml.safe_load(draft_yaml)
        models.JobConfig.model_validate(parsed)
    except Exception:  # noqa: BLE001
        return draft_yaml
    linted = enforce_override_lints(parsed)
    if linted == parsed:
        return draft_yaml
    return yaml.safe_dump(linted, sort_keys=False, allow_unicode=True, width=100).strip()


def rendered_text_for_draft(draft: dict, pool: models.ExperiencePool) -> str:
    """Every string the résumé build will typeset from this draft, one per
    line, in the order ``templates/resume.tex.j2`` renders them:

      headline · summary · per selected entry: role, company, dates, and —
      only when the entry has a location, exactly as the template nests
      them — location and stack · each selected bullet (``bullet_overrides``
      REPLACES the pooled text, the same rule as ``build.resolved_bullets``)
      · each ``skills_emphasis`` group title and item.

    Profile text (name, contact, education) is rendered too but is not the
    draft's to change, so it is deliberately left out — the prune is then
    conservative on a keyword only the profile could satisfy. Ids that do
    not resolve in the pool are skipped; ``validate_draft`` reports them."""
    lines: list[str] = []
    for key in ("headline", "summary"):
        val = draft.get(key)
        if isinstance(val, str):
            lines.append(val)

    overrides = draft.get("bullet_overrides") or {}
    entries_by_id = {e.id: e for e in pool.entries}
    for sel in draft.get("experience_selection") or []:
        entry = entries_by_id.get(sel.get("job_id"))
        if entry is None:
            continue
        lines += [entry.role, entry.company, entry.dates]
        if entry.location:
            lines.append(entry.location)
            if entry.stack:
                lines.append(entry.stack)
        by_id = {b.id: b.text for b in entry.bullets}
        for bid in sel.get("bullets") or []:
            if bid in by_id:
                lines.append(overrides.get(bid, by_id[bid]))

    for group in draft.get("skills_emphasis") or []:
        title = group.get("title")
        if isinstance(title, str):
            lines.append(title)
        lines += [item for item in group.get("items") or [] if isinstance(item, str)]

    return "\n".join(lines)


def _guardrail_finds(rendered_text: str, keyword: str) -> bool:
    """True iff the build's ATS guardrail would count ``keyword`` as present.

    Mirrors ``verify.check_ats_keywords`` by delegating to it, so the prune
    and the guardrail cannot drift: both sides are ``.lower()``-ed and the
    keyword is substring-matched — no whitespace collapse, no tokenising."""
    passed, _ = verify.check_ats_keywords(rendered_text, [keyword])
    return passed


def prune_uncovered_keywords(draft: dict, rendered_text: str) -> dict:
    """Keep a must-have only if the guardrail would find it in
    ``rendered_text``; move the rest to ``dropped_keywords`` (appended after
    any the model already listed, order preserved, de-duplicated). Returns a
    new dict with ``dropped_keywords`` placed right after
    ``must_have_keywords``; the input is not mutated. ``nice_to_have_keywords``
    is left alone — only must-haves fail the build."""
    must = list(draft.get("must_have_keywords") or [])
    kept = [kw for kw in must if _guardrail_finds(rendered_text, kw)]
    newly_dropped = [kw for kw in must if not _guardrail_finds(rendered_text, kw)]
    if not newly_dropped:
        return dict(draft)

    dropped: list[str] = []
    for kw in list(draft.get("dropped_keywords") or []) + newly_dropped:
        if kw not in dropped:
            dropped.append(kw)

    out: dict = {}
    for key, val in draft.items():
        if key == "dropped_keywords":
            continue
        out[key] = kept if key == "must_have_keywords" else val
        if key == "must_have_keywords":
            out["dropped_keywords"] = dropped
    if "dropped_keywords" not in out:
        out["dropped_keywords"] = dropped
    return out


def _prune_draft(draft_yaml: str, pool: models.ExperiencePool) -> str:
    """Enforce must-have coverage on the model's (already capped and
    override-linted) draft.
    Same discipline as ``_cap_draft``: re-serialises only when a keyword is
    dropped; anything malformed passes through untouched so that
    ``validate_draft`` is the one to report it."""
    try:
        parsed = yaml.safe_load(draft_yaml)
        models.JobConfig.model_validate(parsed)
    except Exception:  # noqa: BLE001
        return draft_yaml
    pruned = prune_uncovered_keywords(parsed, rendered_text_for_draft(parsed, pool))
    if pruned == parsed:
        return draft_yaml
    return yaml.safe_dump(pruned, sort_keys=False, allow_unicode=True, width=100).strip()


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
