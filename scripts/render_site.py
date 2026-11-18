#!/usr/bin/env python3
"""Render the experience section of index.html from experience.yaml.

Reads ``resume-generator/data/experience.yaml`` (canonical bullet pool used by
both the resume generator and this site), renders a Jinja2 partial, and splices
the result into ``index.html`` between sentinel comments:

    <!-- EXPERIENCE:START -->
    ... generated markup ...
    <!-- EXPERIENCE:END -->

Run from the repo root via ``make site`` (preferred) or
``uv run --project resume-generator python scripts/render_site.py``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RG_SRC = REPO_ROOT / "resume-generator" / "src"
DATA_DIR = REPO_ROOT / "resume-generator" / "data"
INDEX_HTML = REPO_ROOT / "index.html"
TEMPLATE_DIR = REPO_ROOT / "scripts" / "templates"
TEMPLATE_NAME = "experience_section.html.j2"

SENTINEL_START = "<!-- EXPERIENCE:START -->"
SENTINEL_END = "<!-- EXPERIENCE:END -->"

sys.path.insert(0, str(RG_SRC))

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402
from resume_generator.models import load_experience  # noqa: E402


def render() -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        keep_trailing_newline=False,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    template = env.get_template(TEMPLATE_NAME)
    pool = load_experience(DATA_DIR)
    return template.render(entries=pool.entries)


def splice(html: str, rendered: str) -> str:
    pattern = re.compile(
        rf"({re.escape(SENTINEL_START)}).*?({re.escape(SENTINEL_END)})",
        re.DOTALL,
    )
    if not pattern.search(html):
        raise SystemExit(
            f"sentinels not found in {INDEX_HTML.relative_to(REPO_ROOT)}; "
            f"add\n  {SENTINEL_START}\n  ...\n  {SENTINEL_END}\n"
            "around the experience timeline before running render_site.py"
        )
    replacement = f"{SENTINEL_START}\n{rendered.rstrip()}\n          {SENTINEL_END}"
    return pattern.sub(lambda _m: replacement, html, count=1)


def main() -> int:
    rendered = render()
    html = INDEX_HTML.read_text(encoding="utf-8")
    new_html = splice(html, rendered)
    if new_html == html:
        print(f"no change: {INDEX_HTML.relative_to(REPO_ROOT)}")
        return 0
    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"updated: {INDEX_HTML.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
