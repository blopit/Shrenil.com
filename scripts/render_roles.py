"""Render the role landing pages: one URL per offer, so each can rank and be cited on its own.

    python3 scripts/render_roles.py

Writes forward-deployed-engineer/, ai-agent-development/ and agent-architecture-review/
(each an index.html). The page chrome matches axed/index.html; edit copy in ROLES below,
then re-run. Claims stay in step with the CentrOS page: say what is built and tested,
and leave deployment status to centros/index.html.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://shrenp.com/"
EMAIL = "patel.shrenil@gmail.com"
INTAKE = "Company:\nRole title (or project):\nPosting link:\nComp range (or budget):\nTimeline:\n\n"
NBSP_DOT = "&nbsp;· "


def icon(name: str, cls: str = "i") -> str:
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="../public/images/icons.svg#{name}"/></svg>'


def mailto(subject: str) -> str:
    return f"mailto:{EMAIL}?subject={quote(subject)}&amp;body={quote(INTAKE)}"


PROOF = [
    ("CentrOS", "The multi-agent orchestration platform I build: typed contracts, eval gates, policy lanes and an owner inbox for human approval. 3,980+ tests on main.", "../centros/"),
    ("Faire", "$5M+ GMV from apparel pre-order initiatives across 3+ international markets in 6 months, as a senior frontend engineer.", "../#experience"),
    ("Coursera", "Shipped the iOS course-download feature, lifting completion 20%+ across a 24M+ learner base.", "../#experience"),
    ("AXED", "A WEBTOON Original with 40M+ reads; I negotiated the IP rights deal with Wattpad WEBTOON Studios solo.", "../axed/"),
]

ROLES = [
    {
        "slug": "forward-deployed-engineer",
        "short": "Forward-Deployed",
        "mark": "rocket",
        "sky": "violet",
        "title": "Forward-Deployed AI Engineer — Shren Patel · Canada, Remote",
        "h1": "Forward-Deployed Engineer",
        "sub": "Full-time role" + NBSP_DOT + "Canada, remote",
        "description": "Shren Patel, forward-deployed AI engineer: takes a customer's workflow to a working agent system, with POCs, integrations, evals and human approval gates. Canada remote, EST/PST overlap.",
        "keywords": "forward deployed engineer, forward-deployed AI engineer, FDE, AI solutions engineer, customer-facing AI engineer, agent deployment, Canada remote",
        "claim": "Customer workflow in, <em>working agent system</em> out.",
        "lede": "I sit with the people who do the work, map the process, and build the agent system that takes it over, one gated step at a time. Ten years of shipping software at Coursera, Faire and D2L, plus the operator side: I help run the 23-unit hospitality operation CentrOS is built around, so I know what a workflow looks like from the customer's chair.",
        "what_h": "What I do in the role",
        "what": [
            ("blue", "route", "Map the real workflow", "Shadow the team, write the process down as steps with owners, inputs and failure cases, and agree on which steps an agent may take alone."),
            ("green", "hand", "Keep a human on anything irreversible", "Risk tiers and approval gates before any side effect, with domain experts (legal, accounting, ops) confirming the calls that need them."),
            ("orange", "plug", "Integrate with what they already run", "Typed, scoped, idempotent tool calls into CRMs, inboxes, calendars and internal APIs, with audit logs per call."),
            ("indigo", "gauge", "Prove it with evals, not demos", "Golden datasets from the customer's own cases, regression gates in CI, and traces over cost, latency and failure modes."),
            ("pink", "rocket", "Expand in gates, not a big-bang launch", "POC on one workflow, then widen scope only when the evals and the approval stats say it is safe to."),
        ],
        "how_h": "How an engagement runs",
        "how": [
            ("search", "Discovery", "Process map, success metric and the list of steps an agent must never take alone."),
            ("hammer", "Proof of concept", "One workflow end-to-end on the customer's real data, behind an approval inbox."),
            ("shield-check", "Gated rollout", "Evals and approval rates decide each expansion; rollback is one step."),
            ("file-text", "Handover", "Runbooks, the eval suite and dashboards the customer's team can own."),
        ],
        "schema": "page",
        "mail_subject": "Forward-Deployed Engineer role",
    },
    {
        "slug": "ai-agent-development",
        "short": "Contract builds",
        "mark": "workflow",
        "sky": "violet",
        "title": "Contract AI Agent Development — Shren Patel · Canada, Remote",
        "h1": "AI agent development",
        "sub": "Contract and freelance" + NBSP_DOT + "Canada, remote",
        "description": "Contract AI agent development by Shren Patel: multi-agent workflow automation, RAG pipelines, and MCP and tool integrations, taken from proof of concept to a system your team runs, with human approval on anything irreversible.",
        "keywords": "AI agent development, contract AI engineer, freelance AI agent developer, multi-agent workflow automation, RAG pipeline development, MCP integration, AI automation consultant, Canada",
        "claim": "An agent system <em>built for your workflow</em>, with a human on every irreversible step.",
        "lede": "Freelance and contract builds for companies that want work moved by agents, not a chatbot bolted on. I scope the workflow, build the system on your stack, and hand it over with the evals and runbooks your team needs to own it.",
        "what_h": "What I build",
        "what": [
            ("blue", "workflow", "Multi-agent workflow automation", "Router → executor patterns with specialised agents and fallbacks, moving work across Slack, email, CRMs, calendars and internal APIs."),
            ("cyan", "search", "RAG pipelines", "Retrieval with ranking, freshness and source attribution, on pgvector or OpenSearch, with token-cost discipline built in."),
            ("indigo", "plug", "MCP and tool integrations", "Tool registries with JSON-schema validation, scoped OAuth, retry policy and side-effect logging."),
            ("green", "hand", "Human approval surfaces", "Confidence-gated handoff, reversible operations and an approval inbox, so nothing irreversible runs unreviewed."),
            ("orange", "database", "Durable execution", "Crash-resumable runs on PostgreSQL: checkpoints, retries, rollback and an explicit failure taxonomy per stage."),
        ],
        "how_h": "How a build runs",
        "how": [
            ("search", "Scoping call", "Your workflow, your stack, the success metric and what must stay with a human."),
            ("hammer", "Proof of concept", "One workflow working on your data, so you judge it on results, not slides."),
            ("shield-check", "Production hardening", "Evals, regression gates, tracing and approval gates before wider rollout."),
            ("file-text", "Handover", "Code in your repo, the eval suite, runbooks and a walkthrough for your team."),
        ],
        "schema": "service",
        "service_type": "AI agent development",
        "mail_subject": "Contract AI agent build",
    },
    {
        "slug": "agent-architecture-review",
        "short": "Reviews",
        "mark": "search",
        "sky": "violet",
        "title": "AI Agent Architecture and Eval Review — Shren Patel",
        "h1": "Architecture and eval reviews",
        "sub": "Consulting" + NBSP_DOT + "for agent systems you already run",
        "description": "Architecture, eval and observability reviews of AI agent systems by Shren Patel: reliability, regression gates, tracing, token cost, tool permissions and human-in-the-loop approval design, with findings ranked by risk.",
        "keywords": "AI agent architecture review, LLM eval review, agent observability, AI system audit, LLM reliability consulting, human-in-the-loop design, token cost review",
        "claim": "A second pair of eyes on the agent system <em>you already run</em>.",
        "lede": "For teams with agents live or close to it who want to know where they will break before a customer finds out. I read the code, the traces and the evals, and come back with findings ranked by risk and the order to fix them in.",
        "what_h": "What I look at",
        "what": [
            ("orange", "triangle-alert", "Reliability and failure modes", "Where runs fail silently, what retries hide, and whether a crash mid-run can be resumed or rolled back."),
            ("blue", "gauge", "Evals and regression gates", "Whether your evals catch the regressions you care about, and whether anything blocks a bad prompt or model change from shipping."),
            ("cyan", "activity", "Observability", "Traces over cost, latency and failure modes, and whether an on-call engineer could explain a bad run from them."),
            ("green", "receipt", "Token cost", "Model routing, prompt design, context packing and caching, with the savings estimated per change."),
            ("indigo", "shield-check", "Tool permissions and approvals", "Scopes on every tool, idempotency, audit logs, and which actions should wait for a human."),
        ],
        "how_h": "What you get",
        "how": [
            ("file-text", "Written findings", "Each issue with evidence, its risk and a concrete fix, ranked by impact."),
            ("gauge", "An eval plan", "The cases and gates your system is missing, ready to add to CI."),
            ("zap", "Quick wins vs structural work", "What to fix this week, and what needs a design change."),
            ("users", "A walkthrough", "A call with your team to go through the findings and answer questions."),
        ],
        "schema": "service",
        "service_type": "AI agent architecture and evaluation review",
        "mail_subject": "Agent architecture review",
    },
]


def schema(role: dict) -> str:
    url = f"{SITE}{role['slug']}/"
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Shren Patel", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": role["h1"], "item": url},
        ],
    }
    person = {"@type": "Person", "@id": f"{SITE}#person", "name": "Shren Patel", "url": SITE}
    if role["schema"] == "service":
        main = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": role["h1"],
            "serviceType": role["service_type"],
            "description": role["description"],
            "url": url,
            "provider": person,
            "areaServed": ["CA", "US"],
        }
    else:
        main = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": role["h1"],
            "description": role["description"],
            "url": url,
            "about": person,
        }
    blocks = [json.dumps(b, ensure_ascii=False, indent=2) for b in (crumbs, main)]
    return "\n".join(
        f'    <script type="application/ld+json">\n{b}\n    </script>' for b in blocks
    )


def tile_rows(items) -> str:
    out = []
    for color, ic, title, body in items:
        out.append(
            f'''        <li class="row row--top">
          <span class="tile tile--{color}" aria-hidden="true">{icon(ic)}</span>
          <span class="row__text"><span class="row__title">{title}</span><span class="row__body">{body}</span></span>
        </li>'''
        )
    return "\n".join(out)


def step_rows(items) -> str:
    out = []
    for n, (ic, title, body) in enumerate(items, 1):
        out.append(
            f'''        <li class="row row--top">
          <span class="glyph">{icon(ic)}</span>
          <span class="row__text"><span class="row__title"><span class="nums">{n}.</span> {title}</span><span class="row__sub">{body}</span></span>
        </li>'''
        )
    return "\n".join(out)


def proof_rows() -> str:
    return "\n".join(
        f'        <div class="claim"><dt><a href="{href}">{name}</a></dt><dd>{body}</dd></div>'
        for name, body, href in PROOF
    )


def other_rows(role: dict) -> str:
    out = []
    for r in ROLES:
        if r is role:
            continue
        out.append(
            f'''        <li class="card"><a class="row" href="../{r['slug']}/">
          <span class="tile tile--indigo" aria-hidden="true">{icon(r['mark'])}</span>
          <span class="row__text"><span class="row__title">{r['h1']}</span><span class="row__sub">{r['sub']}</span></span>
          {icon('chevron-right', 'i row__chev')}
        </a></li>'''
        )
    return "\n".join(out)


def page(role: dict) -> str:
    url = f"{SITE}{role['slug']}/"
    mail = mailto(role["mail_subject"])
    og_title = role["title"]
    return f'''<!DOCTYPE html>
<!-- Generated by scripts/render_roles.py; edit the copy there and re-run. -->
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>{role['title']}</title>
    <meta name="description" content="{role['description']}">
    <meta name="keywords" content="{role['keywords']}">
    <meta name="author" content="Shren Patel">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{role['description']}">
    <meta property="og:image" content="{SITE}public/images/og-home.png">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Shren Patel">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{role['description']}">
    <meta name="twitter:image" content="{SITE}public/images/og-home.png">
    <link rel="canonical" href="{url}">
    <meta name="color-scheme" content="dark light">
    <meta name="theme-color" content="#000000">
    <script>
    /* Appearance before first paint; same as the other pages (see axed/index.html). */
    (function (d, w) {{
      var r = d.documentElement, a = null, b = null, q, t, m;
      try {{ a = w.localStorage.getItem('centros.appearance'); b = w.localStorage.getItem('centros.background'); }} catch (e) {{}}
      try {{ q = new URLSearchParams(w.location.search); if (q.has('appearance')) a = q.get('appearance'); if (q.has('background')) b = q.get('background'); }} catch (e) {{}}
      if (a !== 'light' && a !== 'system') a = 'dark';
      t = (a === 'light' || (a === 'system' && w.matchMedia && w.matchMedia('(prefers-color-scheme: light)').matches)) ? 'light' : 'dark';
      r.setAttribute('data-appearance', a);
      r.setAttribute('data-theme', t);
      r.className += (r.className ? ' ' : '') + 'js' + (b === 'solid' ? ' sky-solid' : '');
      m = d.querySelector('meta[name="theme-color"]');
      if (m) m.setAttribute('content', t === 'light' ? '#F2F2F7' : '#000000');
    }})(document, window);
    </script>
{schema(role)}
    <link rel="stylesheet" href="../public/css/style.css">
    <link rel="stylesheet" href="../public/css/sky.css">
    <link rel="stylesheet" href="../public/css/pages/role.css">
    <link rel="icon" href="../public/images/favicon.svg" type="image/svg+xml">
    <script src="../public/js/sky.js" defer></script>
    <script src="../public/js/portfolio.js" defer></script>
  </head>
  <body class="page-role" data-sky="{role['sky']}">
    <a class="skip" href="#main">Skip to content</a>
    <header class="topbar" data-topbar>
      <p class="topbar__title" aria-hidden="true">{role['short']}</p>
      <a class="glass glass-btn topbar__account" href="#contact" data-sheet aria-label="Contact and settings"><span class="avatar avatar--30 av-6" aria-hidden="true">SP</span></a>
    </header>
    <main id="main" class="wrap" tabindex="-1">
    <header class="hero" id="top">
      <div class="lt rl-head">
        <span class="rl-mark" aria-hidden="true">{icon(role['mark'])}</span>
        <div class="rl-head__text"><h1 class="lt__title" data-large-title>{role['h1']}</h1><p class="lt__sub">{role['sub']}</p></div>
      </div>
      <p class="hero__claim">{role['claim']}</p>
      <div class="actions">
        <a class="btn btn--inverse" href="{mail}">{icon('mail')}Email me</a>
        <a class="btn glass" href="../centros/">{icon('arrow-right')}See CentrOS</a>
      </div>
      <div class="card card--text hero__intro rl-lede">
        <p>{role['lede']}</p>
      </div>
    </header>

    <section class="sec" id="what" aria-labelledby="what-h">
      <div class="sec__head">{icon('target', 'i sec__icon')}<h2 class="sec__title" id="what-h">{role['what_h']}</h2><p class="sec__detail">{len(role['what'])}</p></div>
      <ol class="card list list--tile">
{tile_rows(role['what'])}
      </ol>
    </section>

    <section class="sec" id="how" aria-labelledby="how-h">
      <div class="sec__head">{icon('route', 'i sec__icon')}<h2 class="sec__title" id="how-h">{role['how_h']}</h2><p class="sec__detail">{len(role['how'])}</p></div>
      <ol class="card list list--glyph">
{step_rows(role['how'])}
      </ol>
    </section>

    <section class="sec" id="proof" aria-labelledby="proof-h">
      <div class="sec__head">{icon('badge-check', 'i sec__icon')}<h2 class="sec__title" id="proof-h">Proof</h2><p class="sec__detail">{len(PROOF)}</p></div>
      <p class="sec__intro">What I have shipped, with the details one tap away.</p>
      <dl class="card claims">
{proof_rows()}
      </dl>
    </section>

    <section class="sec" id="other" aria-labelledby="other-h">
      <div class="sec__head">{icon('handshake', 'i sec__icon')}<h2 class="sec__title" id="other-h">Other ways to work with me</h2></div>
      <ul class="apart" aria-labelledby="other-h">
{other_rows(role)}
      </ul>
    </section>

    <section class="sec" id="contact" aria-labelledby="contact-h">
      <div class="sec__head">{icon('mail', 'i sec__icon')}<h2 class="sec__title" id="contact-h">Start a conversation</h2></div>
      <p class="sec__intro">Canada, remote, with EST/PST overlap.</p>
      <ul class="card list list--glyph">
        <li class="row">
          <span class="glyph">{icon('mail')}</span>
          <span class="row__text"><span class="row__title">Email</span><a class="row__sub row__link" href="{mail}">{EMAIL}</a></span>
          <span class="row__trail"><button class="pill copy" type="button" data-copy="{EMAIL}" hidden>Copy</button><a class="pill pill--primary" href="{mail}">Email</a><span class="vh" role="status"></span></span>
        </li>
        <li><a class="row" href="https://linkedin.com/in/shrenp" target="_blank" rel="noopener">
          <span class="glyph">{icon('linkedin')}</span>
          <span class="row__text"><span class="row__title">LinkedIn</span><span class="row__sub">linkedin.com/in/shrenp</span></span>
          {icon('arrow-up-right', 'i row__ext')}<span class="vh"> (opens in a new tab)</span>
        </a></li>
        <li><a class="row" href="../#experience">
          <span class="glyph">{icon('briefcase-business')}</span>
          <span class="row__text"><span class="row__title">Full experience</span></span>
          {icon('chevron-right', 'i row__chev')}
        </a></li>
      </ul>
      <p class="sec__foot">I reply to every inquiry that includes the company, a posting link and a comp range or budget. The email button fills in those fields for you.</p>
    </section>

    </main>
    <footer class="foot wrap">
      <p>© <span data-year>2026</span> Shren Patel&nbsp;· built solo, plain HTML&nbsp;· no cookies, no tracking</p>
      <p><a href="../styleguide/">Style guide</a></p>
    </footer>
    <nav class="tabbar" data-tabbar aria-label="Primary">
      <div class="glass tabbar__tabs">
        <span class="tabbar__thumb" aria-hidden="true"></span>
        <a class="tab" href="../">{icon('house')}<span class="tab__label">Home</span></a>
        <a class="tab" href="../centros/">{icon('globe')}<span class="tab__label">CentrOS</span></a>
        <a class="tab" href="../axed/">{icon('book-open')}<span class="tab__label">AXED</span></a>
      </div>
      <a class="glass tabbar__ask" href="{mail}" aria-label="Email Shren">{icon('mail')}</a>
    </nav>
{SHEET.replace(AXED_MAIL, mail)}
  </body>
</html>
'''


def sheet() -> str:
    """The contact-and-settings sheet, copied from axed/index.html so it stays identical."""
    html = (ROOT / "axed" / "index.html").read_text(encoding="utf-8")
    start = html.index('    <dialog class="sheet"')
    end = html.index("</dialog>", start) + len("</dialog>")
    return html[start:end]


def main() -> None:
    global SHEET
    SHEET = sheet()
    for role in ROLES:
        out = ROOT / role["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(role), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")


SHEET = ""
AXED_MAIL = f"mailto:{EMAIL}?subject=Intro%20%E2%80%94%20via%20the%20AXED%20case%20study"

if __name__ == "__main__":
    main()
