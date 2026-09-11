"""Tests for the deterministic bullet cap in ``tailor``.

The 1-page layout overflows past ``MAX_TOTAL_BULLETS`` even at the densest
density tier, and ``build`` then refuses the package. The prompt asks the
model for 7–8 bullets; ``cap_bullet_budget`` is the ceiling that holds when
the model overshoots. ``draft_job_config`` is exercised against a fake
``anthropic`` module so the tests run offline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from resume_generator import models
from resume_generator import tailor as tailor_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sel(job_id: str, n: int) -> models.ExperienceSelection:
    return models.ExperienceSelection(job_id=job_id, bullets=[f"{job_id}-{i}" for i in range(n)])


def _total(selection: list[models.ExperienceSelection]) -> int:
    return sum(len(s.bullets) for s in selection)


# 12 bullets across 4 roles — the shape that broke every package on 2026-09-10.
OVERLONG = [_sel("centros-founder", 5), _sel("conscious-creations", 3), _sel("faire", 2), _sel("coursera", 2)]


# ---------------------------------------------------------------------------
# cap_bullet_budget
# ---------------------------------------------------------------------------


def test_cap_drops_from_the_end_until_eight() -> None:
    capped = tailor_mod.cap_bullet_budget(OVERLONG)

    assert _total(capped) == tailor_mod.MAX_TOTAL_BULLETS == 8
    # First (CentrOS) entry is untouched — drops come from the tail.
    assert capped[0] == OVERLONG[0]
    assert [s.job_id for s in capped] == ["centros-founder", "conscious-creations"]
    assert capped[1].bullets == OVERLONG[1].bullets  # 5 + 3 = 8; faire 2 → 0 and coursera 2 → 0, both removed
    # Input is not mutated.
    assert _total(OVERLONG) == 12


# The exact 9-bullet / 6-role shape that overflowed 1 page on the 2026-09-10
# live run — each role costs a header line on top of its bullets.
LIVE_NINE = [_sel("centros-founder", 3), _sel("conscious-creations", 2), _sel("independent-builder", 1),
             _sel("faire", 1), _sel("webtoon", 1), _sel("coursera", 1)]


def test_cap_reduces_the_live_nine_bullet_six_role_shape_to_eight() -> None:
    capped = tailor_mod.cap_bullet_budget(LIVE_NINE)

    assert _total(capped) == 8
    # The oldest role goes, and takes its header line with it.
    assert [s.job_id for s in capped] == ["centros-founder", "conscious-creations", "independent-builder",
                                          "faire", "webtoon"]
    assert _total(LIVE_NINE) == 9


def test_cap_is_a_no_op_under_budget() -> None:
    within = [_sel("centros-founder", 3), _sel("faire", 2), _sel("coursera", 1)]
    assert tailor_mod.cap_bullet_budget(within) == within


def test_cap_keeps_at_least_one_first_entry_bullet() -> None:
    capped = tailor_mod.cap_bullet_budget([_sel("centros-founder", 2), _sel("faire", 2)], limit=0)
    assert capped == [models.ExperienceSelection(job_id="centros-founder", bullets=["centros-founder-0"])]


# ---------------------------------------------------------------------------
# _cap_draft (string level — what the CLI actually receives)
# ---------------------------------------------------------------------------


def _draft_yaml(selection: list[models.ExperienceSelection]) -> str:
    return yaml.safe_dump(
        {
            "slug": "acme",
            "company": "Acme",
            "role": "Staff AI Engineer",
            "headline": "AI agent orchestration",
            "summary": "Two sentences.",
            "experience_selection": [s.model_dump() for s in selection],
            "bullet_overrides": {"centros-founder-0": "rewritten", "coursera-1": "dropped-but-harmless"},
        },
        sort_keys=False,
    )


def test_cap_draft_passes_compliant_and_malformed_drafts_through_unchanged() -> None:
    compliant = "# a comment the model wrote\n" + _draft_yaml([_sel("centros-founder", 3), _sel("faire", 2)])
    assert tailor_mod._cap_draft(compliant) == compliant  # byte-identical, comment kept
    assert tailor_mod._cap_draft("bad: [yaml") == "bad: [yaml"
    assert tailor_mod._cap_draft("slug: acme\n") == "slug: acme\n"  # schema error → validate_draft's job


def test_cap_draft_truncates_an_overlong_selection() -> None:
    out = tailor_mod._cap_draft(_draft_yaml(OVERLONG))
    job = models.JobConfig.model_validate(yaml.safe_load(out))

    assert _total(job.experience_selection) == 8
    assert job.experience_selection[0].bullets == OVERLONG[0].bullets
    assert job.bullet_overrides == {"centros-founder-0": "rewritten", "coursera-1": "dropped-but-harmless"}


# ---------------------------------------------------------------------------
# draft_job_config — the cap is on the real call path
# ---------------------------------------------------------------------------


def test_draft_job_config_returns_a_capped_draft(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "profile.yaml").write_text("name: Shren\n")
    (tmp_path / "experience.yaml").write_text("entries: []\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    model_reply = "```yaml\n" + _draft_yaml(OVERLONG) + "```"
    fake_response = SimpleNamespace(content=[SimpleNamespace(type="text", text=model_reply)])
    fake_client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_response))
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=lambda api_key: fake_client))

    draft = tailor_mod.draft_job_config("acme", "JD text", tmp_path)
    job = models.JobConfig.model_validate(yaml.safe_load(draft))

    assert _total(job.experience_selection) <= tailor_mod.MAX_TOTAL_BULLETS
    assert job.experience_selection[0].job_id == "centros-founder"
    assert len(job.experience_selection[0].bullets) == 5
