# resume-generator

Internal dev tool. Produces a tailored 1-page resume PDF per target job from
structured YAML, rendered through LaTeX (`tectonic`) and gated by five
build-time guardrails. Also produces a per-job application-form Markdown
report (copy-paste source for Greenhouse / Lever / Ashby) and Claude-drafted
cover letters.

## Install

One-time:

```bash
# macOS
brew install tectonic poppler

# Python deps (recommended via uv)
cd resume-generator
uv sync
```

For the `tailor` and `cover-letter` commands set:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Use

```bash
# --- resume ---
uv run resume list                                        # list configured target jobs
uv run resume build acquia-staff-ai                        # build one
uv run resume build --all                                  # build every job
uv run resume build acquia-staff-ai --update-snapshot      # refresh baseline
uv run resume verify acquia-staff-ai                       # re-run guardrails on existing PDF

# --- application form data ---
uv run resume application acquia-staff-ai                  # print copy-paste Markdown report
uv run resume application acquia-staff-ai -o app.md         # write to file
uv run resume application acquia-staff-ai --stories scale  # filter STAR stories by tag

# --- cover letter ---
uv run resume cover-letter acquia-staff-ai                       # draft, write to data/cover-letters/<slug>.md
uv run resume cover-letter acquia-staff-ai --posting jd.txt      # ground draft on raw JD
uv run resume cover-letter acquia-staff-ai --force               # redraft existing
uv run resume cover-letter acquia-staff-ai --print-only          # preview without writing
uv run resume cover-letter acquia-staff-ai --build-pdf           # compile output/cover-letter-<slug>.pdf

# --- tailor (draft a new <slug>.yaml from a JD) ---
uv run resume tailor my-new-role --posting jd.txt                # prints draft
uv run resume tailor my-new-role --posting jd.txt --write        # writes data/jobs/<slug>.yaml
```

Outputs:
- `output/resume-<slug>.pdf` — 1-page resume (gitignored)
- `output/cover-letter-<slug>.pdf` — 1-page cover letter (gitignored)
- `data/cover-letters/<slug>.md` — Claude-drafted cover letter body (committed)

## How it's wired

| Piece                                  | Purpose                                                 |
| -------------------------------------- | ------------------------------------------------------- |
| `data/profile.yaml`                    | Name, contact, education — static                       |
| `data/skills.yaml`                     | Master skill taxonomy                                   |
| `data/experience.yaml`                 | Every job + every bullet. Each bullet tagged with `keywords` (ATS) and `affinities` (job-slug fit). All bullets ≤30 words, ≥1 digit (enforced by lints). |
| `data/jobs/<slug>.yaml`                | Per-job config: summary, ATS keywords, bullet selection, overrides, skill order, and `application:` overlay (why-company, why-role, custom Qs, per-tech years) |
| `data/application.yaml`                | Universal application data: work auth, comp, logistics, identity/EEO, profile links, referral, STAR stories |
| `data/cover-letters/<slug>.md`         | Claude-drafted cover-letter body per job                |
| `templates/resume.tex.j2`              | Single-column LaTeX resume layout with density-tunable spacing |
| `templates/application.md.j2`          | Markdown report mirroring Greenhouse/Lever/Ashby form sections |
| `templates/cover-letter.tex.j2`        | 1-page LaTeX cover letter (same fontspec as resume)     |
| `src/resume_generator/build.py`        | YAML → Jinja → tectonic, auto-retry at denser tiers; bullet `<<METRIC:>>` placeholder enforcement |
| `src/resume_generator/verify.py`       | The five guardrails                                     |
| `src/resume_generator/application.py`  | Application Markdown renderer + cover-letter PDF compile |
| `src/resume_generator/tailor.py`       | Claude API: draft `<slug>.yaml` from a JD; draft cover-letter prose |

## Guardrails

Every `build` runs these after compile. A failure exits non-zero.

1. **1 page exactly.** Build retries at `normal → compact → ultra` density tiers; if the densest still overflows, fails with the bullet counts so you know what to trim.
2. **ATS keyword coverage.** Every term in the job config's `must_have_keywords` must substring-match (case-insensitive) the `pdftotext` output. Missing terms fail loudly.
3. **Plaintext contact extractable.** Email, phone digits, and every link label must appear in the `pdftotext` output. Catches the LaTeX trap where `\href{}{}` hides the email from ATS parsers.
4. **Bullet lints (2026 content rules).** Every rendered bullet ≤30 words, ≥1 digit, and ideally opens with a strong action verb (allowlist in `verify.STRONG_VERBS`). Length + digit failures fail the build; weak verbs warn. The build also refuses to compile any bullet containing an unfilled `<<METRIC: …>>` placeholder.
5. **Snapshot diff.** `snapshots/<slug>/resume.txt` is committed. Each build re-extracts and surfaces line-level diff; `--update-snapshot` refreshes the baseline.

Plus a soft `resume application <slug>` check that warns when `application.yaml` or the per-job overlay is missing recommended fields (comp range, start date, why-company, etc.) or when STAR stories don't cover the standard tag set (`incident`, `scale`, `failure-modes`, `ownership`, `leadership`, `cross-team`, `ambiguity`, `shipping`).

## Adding a new target job

1. Write `data/jobs/<slug>.yaml` (copy an existing one as a template) **or** run `resume tailor <slug> --posting jd.txt --write` to have Claude draft it from the JD.
2. `resume build <slug>` — fix any guardrail failures.
3. `resume build <slug> --update-snapshot` once it looks right.
4. Commit the YAML + the snapshot directory.

## Adding a new bullet

Edit `data/experience.yaml` — append a new bullet under the right entry with stable `id`, `keywords`, and `affinities`. Follow the 2026 formula: **action verb + tool/method + quantified result + scope**. ≤30 words, ≥1 digit. Then reference it from any job config that should use it.

## Filling out an application

```bash
uv run resume build <slug>                          # PDF ready
uv run resume cover-letter <slug> --build-pdf       # cover-letter PDF ready
uv run resume application <slug> --out app.md       # copy-paste source
```

Open `app.md` in any Markdown viewer (or paste into a Greenhouse/Lever/Ashby form one section at a time). Tweak the per-job answers in `data/jobs/<slug>.yaml` under the `application:` block; tweak universal answers in `data/application.yaml`.

## Why LaTeX (`tectonic`)

`tectonic` is a single hermetic binary — no TeX Live install, no surprise package fetches at build time. Typography is publication-grade, and the PDFs parse cleanly through every ATS we've tested.
