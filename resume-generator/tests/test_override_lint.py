"""Tests for the deterministic ``bullet_overrides`` lint in ``tailor``.

The build's bullet lint (``verify.check_bullet_lints``) fails on any rendered
bullet over 30 words or without a digit. Pool bullets are curated to pass;
the rewrites the model writes into ``bullet_overrides`` are not, and on the
2026-09-10 live run they alone failed 2 of 10 packages. ``enforce_override_lints``
is the check that holds when the prompt doesn't — a failing rewrite is
discarded so the bullet falls back to its pooled text, and the id lands in
``dropped_overrides`` so the discard is visible. It runs BEFORE the keyword
prune so a must-have that lived only in a discarded rewrite is dropped too.
``draft_job_config`` is exercised against a fake ``anthropic`` module so the
tests run offline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from resume_generator import build, models, verify
from resume_generator import tailor as tailor_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


POOL = models.ExperiencePool.model_validate(
    {
        "entries": [
            {
                "id": "centros-founder",
                "role": "Founder",
                "company": "CentrOS",
                "dates": "2024 – present",
                "bullets": [
                    {"id": "centros-0", "text": "Built 4 typed tool contracts with LLM tool-calling."},
                    {"id": "centros-1", "text": "Caught 22 silent regressions with eval gates."},
                ],
            },
        ]
    }
)


def _bullet(n_words: int, *, digit: bool = True, lead: str = "Shipped") -> str:
    """An ``n_words``-word bullet by the build's own tokeniser (``verify._WORD_RE``)."""
    words = [lead] + ["alpha"] * (n_words - 2) + (["100%"] if digit else ["percent"])
    text = " ".join(words) + "."
    assert len(verify._WORD_RE.findall(text)) == n_words
    return text


def _draft(**overrides: object) -> dict:
    base: dict = {
        "slug": "acme",
        "company": "Acme",
        "role": "Staff AI Engineer",
        "headline": "AI agent orchestration",
        "summary": "Ships production Python systems.",
        "must_have_keywords": [],
        "experience_selection": [{"job_id": "centros-founder", "bullets": ["centros-0", "centros-1"]}],
        "bullet_overrides": {},
        "skills_emphasis": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# override_lint_failures — parity with verify.check_bullet_lints
# ---------------------------------------------------------------------------


def test_override_lint_failures_mirror_the_build_lint() -> None:
    thirty_split_words_but_31_tokens = " ".join(["Shipped"] + ["alpha"] * 28 + ["3,980+"])  # "3,980" is 2 tokens
    thirty_one_split_words_but_30_tokens = " ".join(["Shipped"] + ["alpha"] * 28 + ["—", "2x"])  # "—" is none
    cases = [
        (_bullet(30), []),
        (_bullet(31), ["31w (>30)"]),
        (_bullet(12, digit=False), ["no digit"]),
        (_bullet(31, digit=False), ["31w (>30)", "no digit"]),
        (thirty_split_words_but_31_tokens, ["31w (>30)"]),   # counted by the build's regex, not str.split()
        (thirty_one_split_words_but_30_tokens, []),
        ("Shipped tool-calling for 2 teams.", []),           # a hyphenated word is 1 token
    ]
    for text, expect in cases:
        assert tailor_mod.override_lint_failures(text) == expect, text
        # Parity with the build itself — the property that keeps the build green.
        job = models.JobConfig.model_validate(_draft(bullet_overrides={"centros-0": text}))
        passed, detail = verify.check_bullet_lints(job, POOL)
        assert passed is (expect == []), (text, detail)
        for failure in expect:
            assert f"centros-0: {failure}" in detail, (text, detail)


# ---------------------------------------------------------------------------
# enforce_override_lints
# ---------------------------------------------------------------------------


def test_removes_a_31_word_override_and_records_it() -> None:
    draft = _draft(bullet_overrides={"centros-0": _bullet(31), "centros-1": _bullet(20)})
    out = tailor_mod.enforce_override_lints(draft)

    assert out["bullet_overrides"] == {"centros-1": _bullet(20)}
    assert out["dropped_overrides"] == ["centros-0"]
    keys = list(out)
    assert keys.index("dropped_overrides") == keys.index("bullet_overrides") + 1
    # Input is not mutated.
    assert set(draft["bullet_overrides"]) == {"centros-0", "centros-1"}
    assert "dropped_overrides" not in draft


def test_keeps_a_30_word_override() -> None:
    draft = _draft(bullet_overrides={"centros-0": _bullet(30)})
    out = tailor_mod.enforce_override_lints(draft)

    assert out == draft
    assert "dropped_overrides" not in out


def test_removes_a_digitless_override() -> None:
    out = tailor_mod.enforce_override_lints(_draft(bullet_overrides={"centros-0": _bullet(12, digit=False)}))

    assert out["bullet_overrides"] == {}
    assert out["dropped_overrides"] == ["centros-0"]


def test_appends_to_an_existing_dropped_overrides_list_preserving_order() -> None:
    out = tailor_mod.enforce_override_lints(_draft(
        bullet_overrides={"centros-0": _bullet(31), "centros-1": _bullet(12, digit=False)},
        dropped_overrides=["centros-1", "centros-9"],  # already listed, one also failing now
    ))

    assert out["dropped_overrides"] == ["centros-1", "centros-9", "centros-0"]


# ---------------------------------------------------------------------------
# _lint_overrides_draft (string level — what the CLI actually receives)
# ---------------------------------------------------------------------------


def _draft_yaml(**overrides: object) -> str:
    return yaml.safe_dump(_draft(**overrides), sort_keys=False, allow_unicode=True)


def test_lint_overrides_draft_passes_compliant_and_malformed_drafts_through_unchanged() -> None:
    compliant = "# a comment the model wrote\n" + _draft_yaml(bullet_overrides={"centros-0": _bullet(30)})
    assert tailor_mod._lint_overrides_draft(compliant) == compliant  # byte-identical, comment kept
    assert tailor_mod._lint_overrides_draft("bad: [yaml") == "bad: [yaml"
    assert tailor_mod._lint_overrides_draft("slug: acme\n") == "slug: acme\n"  # schema error → validate_draft's job


def test_lint_overrides_draft_rewrites_a_failing_draft_into_a_valid_job_config() -> None:
    out = tailor_mod._lint_overrides_draft(_draft_yaml(bullet_overrides={"centros-0": _bullet(31)}))
    job = models.JobConfig.model_validate(yaml.safe_load(out))

    assert job.bullet_overrides == {}
    assert job.dropped_overrides == ["centros-0"]


def test_job_config_schema_accepts_and_defaults_dropped_overrides() -> None:
    assert models.JobConfig.model_validate(_draft()).dropped_overrides == []
    assert models.JobConfig.model_validate(_draft(dropped_overrides=["x"])).dropped_overrides == ["x"]


def test_build_renders_the_pooled_text_for_a_dropped_override() -> None:
    # The field is a record, not an instruction: build.py never reads it.
    job = models.JobConfig.model_validate(_draft(dropped_overrides=["centros-0"]))
    texts = [text for _, bid, text in build.resolved_bullets(job, POOL) if bid == "centros-0"]
    assert texts == ["Built 4 typed tool contracts with LLM tool-calling."]


# ---------------------------------------------------------------------------
# draft_job_config — the lint is on the real call path, BEFORE the prune
# ---------------------------------------------------------------------------


def test_lint_runs_before_prune_so_a_keyword_only_in_a_dropped_override_is_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "profile.yaml").write_text("name: Shren\n")
    (tmp_path / "experience.yaml").write_text(yaml.safe_dump(POOL.model_dump()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # "Kubernetes" appears ONLY in the 31-word rewrite; the pooled centros-0 text lacks it.
    model_reply = "```yaml\n" + _draft_yaml(
        must_have_keywords=["Kubernetes", "LLM"],
        bullet_overrides={"centros-0": _bullet(31, lead="Kubernetes")},
    ) + "```"
    fake_response = SimpleNamespace(content=[SimpleNamespace(type="text", text=model_reply)])
    fake_client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_response))
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=lambda api_key: fake_client))

    draft = tailor_mod.draft_job_config("acme", "JD text", tmp_path)
    job = models.JobConfig.model_validate(yaml.safe_load(draft))

    assert job.bullet_overrides == {}
    assert job.dropped_overrides == ["centros-0"]
    # Pruned against the text that survives — had the prune run first it would
    # have seen "Kubernetes" in the rewrite and left a must-have the build lacks.
    assert job.must_have_keywords == ["LLM"]
    assert job.dropped_keywords == ["Kubernetes"]
