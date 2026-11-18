"""Phase 3 deliverables: maturity reframe, AXED case study, social-proof
scaffold, demo placeholder.

Each test encodes one success criterion from the plan. Tests live at the site
root because they validate site-level artifacts (HTML + ancillary files), not
the resume-generator package.

Run from the repo root:

    uv run --with pytest pytest tests/ -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Phase 3.1 — CentrOS maturity reframe + Traction
# ---------------------------------------------------------------------------


class TestCentrOSMaturityReframe:
    def test_traction_section_exists(self, centros_html: str) -> None:
        """CentrOS page should have a dedicated Traction subsection with concrete numbers."""
        assert re.search(r'id="traction"', centros_html, re.IGNORECASE), (
            "centros/index.html should expose <section id=\"traction\"> "
            "(Phase 3.1 — surfaces concrete traction signals so 'v0.4' "
            "doesn't read as the only quantification)."
        )

    def test_traction_section_has_specific_numbers(
        self, centros_html: str, repo_root: Path
    ) -> None:
        """The traction section must contain at least 3 concrete numbers
        (deploy frequency, test count, units served, etc.)."""
        traction_match = re.search(
            r'id="traction".*?</section>',
            centros_html,
            re.DOTALL | re.IGNORECASE,
        )
        assert traction_match, "could not locate traction section bounds"
        traction = traction_match.group(0)
        numbers = re.findall(r"\b\d[\d,]*\+?\b", traction)
        assert len(numbers) >= 3, (
            f"traction section should expose ≥3 concrete numbers; found {len(numbers)}: {numbers}"
        )

    def test_no_v04_in_user_facing_copy(
        self, centros_html: str, index_html: str
    ) -> None:
        """'v0.4' shouldn't appear in user-facing HTML (machine-readable
        JSON-LD softwareVersion is fine; visible body copy is not)."""
        body_pattern = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL | re.IGNORECASE)
        for label, html in (("centros", centros_html), ("index", index_html)):
            m = body_pattern.search(html)
            assert m, f"could not locate <body> in {label}.html"
            assert "v0.4" not in m.group(1), (
                f"{label}/index.html body still contains 'v0.4' — read as early-stage "
                "to staff-level recruiters. Reframe as 'Production' or drop the version."
            )

    def test_no_dogfood_in_user_facing_copy(
        self, centros_html: str, index_html: str
    ) -> None:
        """'dogfood' / 'dogfooded' is engineer jargon that reads weakly to AE
        recruiters. Should not appear in rendered HTML body."""
        body_pattern = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL | re.IGNORECASE)
        for label, html in (("centros", centros_html), ("index", index_html)):
            m = body_pattern.search(html)
            body = m.group(1).lower() if m else ""
            assert "dogfood" not in body, (
                f"{label}/index.html body contains 'dogfood' — reframe as "
                "'production deployment' or 'runs on'."
            )

    def test_no_apologetic_phrases(
        self, centros_html: str, index_html: str
    ) -> None:
        """Self-disqualifying phrases should not appear anywhere visible."""
        forbidden = [
            "not a fit",
            "would be a mismatch",
            "honest answer",
            "not a traditional",
            "rather be honest",
            "submitting in case",
            "submitting only if",
            "platform is 4 months old",
        ]
        for label, html in (("centros", centros_html), ("index", index_html)):
            lowered = html.lower()
            for phrase in forbidden:
                assert phrase.lower() not in lowered, (
                    f"{label}/index.html contains apologetic phrase: {phrase!r}"
                )


# ---------------------------------------------------------------------------
# Phase 3.4 — AXED as first-class artifact
# ---------------------------------------------------------------------------


class TestAXEDCaseStudyPage:
    def test_page_exists(self, repo_root: Path) -> None:
        assert (repo_root / "axed" / "index.html").exists(), (
            "axed/index.html should exist (Phase 3.4 — AXED is the strongest "
            "single proof point for non-engineering audiences)."
        )

    def test_has_three_required_sections(self, axed_html: str) -> None:
        """Product / business outcome / what it proves about Shren."""
        assert axed_html, "axed/index.html missing"
        required_ids = ["product", "outcome", "proves"]
        for slug in required_ids:
            assert re.search(rf'id="{slug}"', axed_html, re.IGNORECASE), (
                f"axed/index.html needs <section id=\"{slug}\"> "
                "(product / business outcome / what it proves)."
            )

    def test_names_wattpad_webtoon_studios(self, axed_html: str) -> None:
        """Single named counterparty for the IP deal."""
        assert axed_html, "axed/index.html missing"
        assert "Wattpad WEBTOON Studios" in axed_html, (
            "axed/index.html should name 'Wattpad WEBTOON Studios' as the IP rights buyer."
        )

    def test_quantifies_reach(self, axed_html: str) -> None:
        """Reads, subscribers, monthly views must appear as concrete numbers."""
        assert axed_html, "axed/index.html missing"
        assert re.search(r"40\s*M\+?|40,000,000", axed_html), (
            "axed/index.html should cite 40M+ reads"
        )
        assert re.search(r"492\s*K\+?|492,000", axed_html), (
            "axed/index.html should cite 492K+ subscribers"
        )

    def test_index_links_to_axed(self, index_html: str) -> None:
        assert re.search(r'href="(\.?/?)axed/?"', index_html), (
            "index.html should link to the AXED case-study page"
        )

    def test_centros_links_to_axed(self, centros_html: str) -> None:
        assert re.search(r'href="(\.\./|/)axed/?"', centros_html), (
            "centros/index.html should link to the AXED case-study page"
        )


# ---------------------------------------------------------------------------
# Phase 3.3 — Social proof scaffold
# ---------------------------------------------------------------------------


class TestSocialProofScaffold:
    def test_outreach_templates_exist(self, repo_root: Path) -> None:
        outreach = repo_root / "scripts" / "outreach"
        assert outreach.exists(), "scripts/outreach/ should exist"
        for name in ("peer.md", "manager.md", "customer.md", "targets.md"):
            assert (outreach / name).exists(), f"scripts/outreach/{name} missing"

    def test_outreach_templates_non_trivial(self, repo_root: Path) -> None:
        """Templates must be substantive, not empty stubs."""
        outreach = repo_root / "scripts" / "outreach"
        for name in ("peer.md", "manager.md", "customer.md"):
            content = (outreach / name).read_text(encoding="utf-8")
            assert len(content) > 300, (
                f"scripts/outreach/{name} should be a real email template "
                f"(>300 chars); got {len(content)}"
            )
            # Templates must have an explicit subject line and a placeholder for the recipient's name.
            assert "Subject:" in content or "subject:" in content.lower(), (
                f"{name} should specify a Subject: line"
            )
            assert "{{" in content or "[" in content, (
                f"{name} should include placeholder tokens (e.g. {{name}} or [Name]) "
                "so it's a template, not a finished message."
            )

    def test_references_section_on_index(self, index_html: str) -> None:
        assert re.search(r'id="references"', index_html, re.IGNORECASE), (
            "index.html should expose <section id=\"references\"> "
            "(Phase 3.3 — empty scaffold ready for real quotes)."
        )

    def test_references_page_exists(self, repo_root: Path) -> None:
        assert (repo_root / "references" / "index.html").exists(), (
            "references/index.html should exist as the private page linked "
            "from cover letters."
        )

    def test_references_page_not_indexed(self, references_html: str) -> None:
        """The references page should ask crawlers not to index it
        (it lists named professional contacts)."""
        assert references_html, "references/index.html missing"
        assert re.search(
            r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex',
            references_html,
            re.IGNORECASE,
        ), "references/index.html should include <meta name=\"robots\" content=\"noindex\">"


# ---------------------------------------------------------------------------
# Phase 3.2 — Demo video placeholder
# ---------------------------------------------------------------------------


class TestDemoVideoMarkup:
    def test_demo_markup_present(self, index_html: str) -> None:
        """Demo video markup should exist somewhere on the index page. A
        DEMO:TODO comment counts as a valid placeholder since the actual
        recording is a human task."""
        has_video = bool(
            re.search(r"<video[\s>]", index_html, re.IGNORECASE)
            or re.search(r"https?://(www\.)?(youtube|loom)\.com", index_html)
            or "DEMO:TODO" in index_html
        )
        assert has_video, (
            "index.html should contain video markup (<video>, YouTube/Loom embed) "
            "or a DEMO:TODO marker so we don't forget to record the demo."
        )


# ---------------------------------------------------------------------------
# Role landing pages — one URL per offer, each indexable on its own
# ---------------------------------------------------------------------------

ROLE_SLUGS = ("forward-deployed-engineer", "ai-agent-development", "agent-architecture-review")


@pytest.mark.parametrize("slug", ROLE_SLUGS)
def test_role_page_is_indexable(slug: str, repo_root: Path, index_html: str) -> None:
    html = (repo_root / slug / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="https://shrenp.com/{slug}/">' in html
    assert "noindex" not in html
    assert 'href="tel:' not in html, "phone number stays off public pages"
    assert f"<loc>https://shrenp.com/{slug}/</loc>" in (repo_root / "sitemap.xml").read_text(encoding="utf-8")
    assert f'href="{slug}/"' in index_html, "homepage should link to each role page"
