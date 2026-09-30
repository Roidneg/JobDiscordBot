from __future__ import annotations

from dataclasses import dataclass
import re

from src.models import Job



@dataclass(frozen=True)
class ScoredJob:
    job: Job
    score: int
    reasons: tuple[str, ...]
    categories: tuple[str, ...]


def _haystack(job: Job) -> str:
    metadata = " ".join(str(v) for v in job.metadata.values())
    return f" {job.title} {job.location} {job.description} {metadata} ".lower()


def is_remote(job: Job) -> bool:
    workplace_type = str(
        job.metadata.get("workplace_type", "")
    ).lower()

    location_text = (
        f"{job.location} {workplace_type}"
    ).lower()

    remote_terms = (
        "remote",
        "distributed",
        "work from home",
        "anywhere",
    )

    return any(
        term in location_text
        for term in remote_terms
    )


def title_is_relevant(job: Job, config: dict) -> bool:
    title = job.title.lower()

    excluded = [str(x).lower() for x in config.get("excluded_title_terms", [])]
    if any(term in title for term in excluded):
        return False

    required = [str(x).lower() for x in config.get("title_terms", [])]
    return not required or any(term in title for term in required)


def location_is_allowed(
    job: Job,
    config: dict,
) -> bool:
    location = job.location.lower()

    allowed = [
        str(term).lower()
        for term in config.get(
            "allowed_location_terms",
            [],
        )
    ]

    if allowed:
        return any(
            re.search(rf"(?<!\w){re.escape(term)}(?!\w)", location)
            for term in allowed
        )

    excluded = [
        str(term).lower()
        for term in config.get(
            "excluded_location_terms",
            [],
        )
    ]

    return not any(
        term in location
        for term in excluded
    )

def get_matching_categories(
    job: Job,
    config: dict,
) -> list[str]:

    title = job.title.lower()
    matches = []

    categories = config.get("categories") or {}

    for category_name, category_config in categories.items():
        terms = category_config.get("title_terms") or []

        if any(
            str(term).lower() in title
            for term in terms
        ):
            matches.append(category_name)

    return matches

def score_job(job: Job, config: dict) -> ScoredJob | None:
    if not title_is_relevant(job, config):
        return None

    if not location_is_allowed(job, config):
        return None

    if config.get("require_remote", False) and not is_remote(job):
        return None

    categories = get_matching_categories(
        job,
        config,
    )

    if not categories:
        return None

    text = _haystack(job)
    score = 0
    reasons: list[str] = []

    for phrase, weight in (config.get("weights") or {}).items():
        phrase_l = str(phrase).lower()
        if phrase_l in text:
            points = int(weight)
            score += points
            clean = phrase_l.strip()
            if clean and clean not in reasons:
                reasons.append(clean)

    if score < int(config.get("minimum_score", 0)):
        return None

    return ScoredJob(
        job=job,
        score=score,
        reasons=tuple(reasons[:6]),
        categories=tuple(categories),
    )
