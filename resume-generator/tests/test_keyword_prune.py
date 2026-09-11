"""Tests for the deterministic must-have keyword prune in ``tailor``.

The build's ATS guardrail (``verify.check_ats_keywords``) fails on any
``must_have_keywords`` term the pdftotext extraction lacks. The prompt asks
the model to list only terms it has placed; ``prune_uncovered_keywords`` is
the check that holds when it doesn't — uncovered must-haves move to
``dropped_keywords`` so the gap is visible instead of failing the build.
``draft_job_config`` is exercised against a fake ``anthropic`` module so the
tests run offline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from resume_generator import models, verify
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
                "location": "Toronto",
                "stack": "TypeScript · Hono",
                "bullets": [
                    {"id": "centros-0", "text": "Built 4 typed tool contracts with LLM tool-calling."},
                    {"id": "centros-1", "text": "Caught 22 silent regressions with eval gates."},
                ],
            },
            {
                "id": "faire",
                "role": "Software Engineer",
                "company": "Faire",
                "dates": "2020",  # no location → the template does not render the stack line
                "stack": "Kotlin · GraphQL",
                "bullets": [{"id": "faire-0", "text": "Shipped 3 apparel features in Java."}],
            },
        ]
    }
)


def _draft(**overrides: object) -> dict:
    base: dict = {
        "slug": "acme",
        "company": "Acme",
        "role": "Staff AI Engineer",
        "headline": "AI agent orchestration",
        "summary": "Ships production Python systems.",
        "must_have_keywords": [],
        "nice_to_have_keywords": ["RAG", "nowhere-nice"],
        "experience_selection": [
            {"job_id": "centros-founder", "bullets": ["centros-0", "centros-1"]},
            {"job_id": "faire", "bullets": ["faire-0"]},
        ],
        "bullet_overrides": {},
        "skills_emphasis": [],
    }
    base.update(overrides)
    return base


def _prune(draft: dict) -> dict:
    return tailor_mod.prune_uncovered_keywords(draft, tailor_mod.rendered_text_for_draft(draft, POOL))


# ---------------------------------------------------------------------------
# rendered_text_for_draft — mirrors what templates/resume.tex.j2 typesets
# ---------------------------------------------------------------------------


def test_rendered_text_mirrors_the_template() -> None:
    draft = _draft(
        bullet_overrides={"centros-0": "Ran 12 Kubernetes rollouts."},
        skills_emphasis=[{"title": "Infra", "items": ["Terraform · AWS"]}],
    )
    text = tailor_mod.rendered_text_for_draft(draft, POOL)

    for present in ("AI agent orchestration", "Ships production Python", "Founder", "CentrOS",
                    "2024 – present", "Toronto", "Hono", "Kubernetes", "eval gates",
                    "Software Engineer", "Faire", "apparel", "Infra", "Terraform"):
        assert present in text, present
    assert "tool-calling" not in text  # the override REPLACES the pooled text
    assert "Kotlin" not in text        # stack is nested under `if entry.location` in the template
    assert "RAG" not in text           # keyword lists are not rendered

    # Unknown ids are skipped, not fatal — validate_draft is the one to report them.
    stray = _draft(experience_selection=[{"job_id": "nope", "bullets": ["x"]},
                                         {"job_id": "faire", "bullets": ["faire-0", "faire-9"]}])
    assert "apparel" in tailor_mod.rendered_text_for_draft(stray, POOL)


# ---------------------------------------------------------------------------
# prune_uncovered_keywords
# ---------------------------------------------------------------------------


def test_keeps_a_must_have_present_only_in_a_bullet_override() -> None:
    out = _prune(_draft(
        must_have_keywords=["Kubernetes", "tool-calling"],
        bullet_overrides={"centros-0": "Ran 12 Kubernetes rollouts."},
    ))
    assert out["must_have_keywords"] == ["Kubernetes"]
    assert out["dropped_keywords"] == ["tool-calling"]  # only in the text the override replaced


def test_keeps_a_must_have_present_only_in_skills_emphasis() -> None:
    out = _prune(_draft(
        must_have_keywords=["Terraform", "Infra"],
        skills_emphasis=[{"title": "Infra", "items": ["Terraform · AWS"]}],
    ))
    assert out["must_have_keywords"] == ["Terraform", "Infra"]
    assert "dropped_keywords" not in out


def test_moves_uncovered_must_haves_to_dropped_keywords_preserving_order() -> None:
    draft = _draft(
        must_have_keywords=["LLM", "generative models", "Python", "JavaScript", "eval", "system design"],
        dropped_keywords=["JavaScript", "Rust"],  # the model's own list, one term also claimed above
    )
    out = _prune(draft)

    assert out["must_have_keywords"] == ["LLM", "Python", "eval"]
    assert out["dropped_keywords"] == ["JavaScript", "Rust", "generative models", "system design"]
    assert out["nice_to_have_keywords"] == ["RAG", "nowhere-nice"]  # nice-to-haves are never pruned
    keys = list(out)
    assert keys.index("dropped_keywords") == keys.index("must_have_keywords") + 1
    # Input is not mutated.
    assert len(draft["must_have_keywords"]) == 6
    assert draft["dropped_keywords"] == ["JavaScript", "Rust"]


def test_normalisation_matches_the_ats_guardrail() -> None:
    cases = [
        ("Shipped JavaScript tooling", "javascript", True),   # case-insensitive both ways
        ("shipped javascript tooling", "JavaScript", True),
        ("LLM tool-calling.", "tool-calling", True),           # substring, punctuation kept
        ("system  design", "system design", False),           # NO whitespace collapse
        ("system\ndesign", "system design", False),           # a line break is not a space
        ("Javascript", "JavaScript", True),
    ]
    for text, kw, expect_kept in cases:
        out = tailor_mod.prune_uncovered_keywords({"must_have_keywords": [kw]}, text)
        kept = out["must_have_keywords"] == [kw] and "dropped_keywords" not in out
        assert kept is expect_kept, (text, kw)
        # Parity with the guardrail itself — the property that keeps the build green.
        assert kept is verify.check_ats_keywords(text, [kw])[0], (text, kw)


# ---------------------------------------------------------------------------
# _prune_draft (string level — what the CLI actually receives)
# ---------------------------------------------------------------------------


def _draft_yaml(**overrides: object) -> str:
    return yaml.safe_dump(_draft(**overrides), sort_keys=False, allow_unicode=True)


def test_prune_draft_passes_covered_and_malformed_drafts_through_unchanged() -> None:
    covered = "# a comment the model wrote\n" + _draft_yaml(must_have_keywords=["LLM", "python", "Toronto"])
    assert tailor_mod._prune_draft(covered, POOL) == covered  # byte-identical, comment kept
    honest = _draft_yaml(must_have_keywords=["LLM"], dropped_keywords=["Rust"])
    assert tailor_mod._prune_draft(honest, POOL) == honest    # the model's own list is left as-is
    assert tailor_mod._prune_draft("bad: [yaml", POOL) == "bad: [yaml"
    assert tailor_mod._prune_draft("slug: acme\n", POOL) == "slug: acme\n"  # schema error → validate_draft's job


def test_prune_draft_rewrites_an_uncovered_draft_into_a_valid_job_config() -> None:
    out = tailor_mod._prune_draft(_draft_yaml(must_have_keywords=["LLM", "system design"]), POOL)
    job = models.JobConfig.model_validate(yaml.safe_load(out))

    assert job.must_have_keywords == ["LLM"]
    assert job.dropped_keywords == ["system design"]
    assert job.nice_to_have_keywords == ["RAG", "nowhere-nice"]


def test_job_config_schema_accepts_and_defaults_dropped_keywords() -> None:
    assert models.JobConfig.model_validate(_draft()).dropped_keywords == []
    assert models.JobConfig.model_validate(_draft(dropped_keywords=["x"])).dropped_keywords == ["x"]


# ---------------------------------------------------------------------------
# draft_job_config — the prune is on the real call path
# ---------------------------------------------------------------------------


def test_draft_job_config_returns_a_pruned_draft(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "profile.yaml").write_text("name: Shren\n")
    (tmp_path / "experience.yaml").write_text(yaml.safe_dump(POOL.model_dump()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    model_reply = "```yaml\n" + _draft_yaml(must_have_keywords=["LLM", "Python", "system design"]) + "```"
    fake_response = SimpleNamespace(content=[SimpleNamespace(type="text", text=model_reply)])
    fake_client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_response))
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=lambda api_key: fake_client))

    draft = tailor_mod.draft_job_config("acme", "JD text", tmp_path)
    parsed = yaml.safe_load(draft)
    job = models.JobConfig.model_validate(parsed)

    assert job.must_have_keywords == ["LLM", "Python"]
    assert job.dropped_keywords == ["system design"]
    assert list(parsed).index("dropped_keywords") == list(parsed).index("must_have_keywords") + 1
