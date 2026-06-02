"""Pydantic schemas for the YAML data files.

The shape is intentionally flat and explicit — these YAMLs are hand-edited and
sometimes Claude-drafted, so error messages need to be unambiguous.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# profile.yaml
# ---------------------------------------------------------------------------


class ContactLink(BaseModel):
    label: str
    url: str


class Contact(BaseModel):
    email: str
    phone: str
    location: str
    links: list[ContactLink] = Field(default_factory=list)


class EducationEntry(BaseModel):
    school: str
    degree: str
    years: str
    location: str | None = None


class Profile(BaseModel):
    name: str
    default_headline: str
    contact: Contact
    education: list[EducationEntry]


# ---------------------------------------------------------------------------
# skills.yaml
# ---------------------------------------------------------------------------


class SkillGroup(BaseModel):
    title: str
    items: list[str]


class SkillsCatalog(BaseModel):
    """Master skill taxonomy. Per-job configs reference these by group title or
    override with their own `skills_emphasis` block."""

    groups: list[SkillGroup]


# ---------------------------------------------------------------------------
# experience.yaml
# ---------------------------------------------------------------------------


class Bullet(BaseModel):
    id: str
    text: str
    keywords: list[str] = Field(default_factory=list)
    affinities: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    id: str
    role: str
    company: str
    dates: str
    location: str | None = None
    stack: str | None = None
    bullets: list[Bullet]


class ExperiencePool(BaseModel):
    entries: list[ExperienceEntry]

    def find_entry(self, job_id: str) -> ExperienceEntry:
        for e in self.entries:
            if e.id == job_id:
                return e
        raise KeyError(f"experience entry not found: {job_id}")


# ---------------------------------------------------------------------------
# jobs/<slug>.yaml
# ---------------------------------------------------------------------------


class ExperienceSelection(BaseModel):
    job_id: str
    bullets: list[str]


class JobConfig(BaseModel):
    slug: str
    company: str
    role: str
    posting_url: str | None = None
    headline: str
    summary: str
    must_have_keywords: list[str] = Field(default_factory=list)
    nice_to_have_keywords: list[str] = Field(default_factory=list)
    experience_selection: list[ExperienceSelection]
    bullet_overrides: dict[str, str] = Field(default_factory=dict)
    skills_emphasis: list[SkillGroup] = Field(default_factory=list)
    application: "JobApplicationOverlay | None" = None


# ---------------------------------------------------------------------------
# application.yaml (universal) + jobs/<slug>.yaml :: application: (per-job)
# ---------------------------------------------------------------------------


class WorkAuthCountry(BaseModel):
    authorized: bool
    requires_sponsorship: bool = False
    visa_type: str | None = None
    notes: str | None = None


class WorkAuthorization(BaseModel):
    countries: dict[str, WorkAuthCountry] = Field(default_factory=dict)


class Compensation(BaseModel):
    currency: str = "USD"
    base_floor: int | None = None
    base_target: int | None = None
    base_ceiling: int | None = None
    total_target: int | None = None
    willing_to_disclose_current: bool = False
    open_to_contract: bool = False
    notes: str | None = None


class Logistics(BaseModel):
    current_location: str
    preferred_timezone_band: str
    willing_to_relocate: bool = False
    remote_only: bool = True
    earliest_start_date: str | None = None
    notice_period_weeks: int | None = None
    travel_willingness: str | None = None


class Identity(BaseModel):
    pronouns: str | None = None
    gender: str | None = None
    race_ethnicity: str | None = None
    hispanic_or_latino: str | None = None
    nationality: str | None = None
    veteran_status: str | None = None
    disability_status: str | None = None
    lgbtq: str | None = None


class ProfileLinks(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    resume_repo: str | None = None
    twitter: str | None = None
    bluesky: str | None = None
    scholar: str | None = None
    stackoverflow: str | None = None


class Referral(BaseModel):
    default_source: str = "Company website / careers page"
    default_referrer: str | None = None


class Story(BaseModel):
    id: str
    prompt: str
    situation: str
    task: str
    action: str
    result: str
    tags: list[str] = Field(default_factory=list)


class Application(BaseModel):
    work_authorization: WorkAuthorization
    compensation: Compensation
    logistics: Logistics
    identity: Identity = Field(default_factory=Identity)
    profile_links: ProfileLinks = Field(default_factory=ProfileLinks)
    referral: Referral = Field(default_factory=Referral)
    stories: list[Story] = Field(default_factory=list)

    def stories_for_tags(self, tags: list[str]) -> list[Story]:
        if not tags:
            return self.stories
        wanted = {t.lower() for t in tags}
        return [s for s in self.stories if wanted & {t.lower() for t in s.tags}]


class CoverLetterConfig(BaseModel):
    """Draft-hints only. The actual body lives in data/cover-letters/<slug>.md
    so it can be hand-edited as plain markdown without YAML escaping."""

    tone: str = "direct, technical, warm"
    paragraphs: int = 3
    must_mention: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class CustomQuestion(BaseModel):
    q: str
    a: str
    char_limit: int | None = None


class JobApplicationOverlay(BaseModel):
    why_company: str | None = None
    why_role: str | None = None
    cover_letter: CoverLetterConfig = Field(default_factory=CoverLetterConfig)
    referral_override: str | None = None
    custom_questions: list[CustomQuestion] = Field(default_factory=list)
    years_experience: dict[str, int] = Field(default_factory=dict)
    notes: str | None = None


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_profile(data_dir: Path) -> Profile:
    return Profile.model_validate(_load_yaml(data_dir / "profile.yaml"))


def load_skills(data_dir: Path) -> SkillsCatalog:
    return SkillsCatalog.model_validate(_load_yaml(data_dir / "skills.yaml"))


def load_experience(data_dir: Path) -> ExperiencePool:
    raw = _load_yaml(data_dir / "experience.yaml")
    if isinstance(raw, list):
        raw = {"entries": raw}
    return ExperiencePool.model_validate(raw)


def load_job(data_dir: Path, slug: str) -> JobConfig:
    path = data_dir / "jobs" / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no job config at {path}")
    return JobConfig.model_validate(_load_yaml(path))


def list_job_slugs(data_dir: Path) -> list[str]:
    return sorted(p.stem for p in (data_dir / "jobs").glob("*.yaml"))


def load_application(data_dir: Path) -> Application:
    path = data_dir / "application.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"no application data at {path} — create it (template in README)"
        )
    return Application.model_validate(_load_yaml(path))


# resolve the forward reference in JobConfig.application
JobConfig.model_rebuild()
