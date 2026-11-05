from __future__ import annotations

import html
import re

import requests

from src.models import Job


BASE_URL = "https://remotive.com/api/remote-jobs"


def _plain_text(value: str) -> str:
    """Remove HTML tags and tidy up whitespace."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def collect_remotive(timeout: int = 20) -> list[Job]:
    """Fetch Remotive listings and convert them into Job objects."""
    response = requests.get(
        BASE_URL,
        timeout=timeout,
        headers={
            "Accept": "application/json",
            "User-Agent": "discord-job-intelligence/0.1",
        },
    )

    response.raise_for_status()
    data = response.json()
    jobs = []

    for item in data.get("jobs") or []:
        job_id = item.get("id")
        title = (item.get("title") or "").strip()
        company = (item.get("company_name") or "").strip()
        url = (item.get("url") or "").strip()

        # Skip incomplete listings that can't be displayed reliably.
        if job_id is None or not title or not company or not url:
            continue

        restriction = (
            item.get("candidate_required_location") or "Not specified"
        ).strip()

        # Keep the source's restriction visible for readers to review.
        if restriction.lower() == "worldwide":
            location = "Remote - Worldwide (US eligibility not verified)"
        else:
            location = f"Remote - {restriction}"

        jobs.append(
            Job(
                job_id=f"remotive:{job_id}",
                title=title,
                company=company,
                location=location,
                url=url,
                source="Remotive",
                description=_plain_text(item.get("description") or ""),
                compensation=(item.get("salary") or "").strip(),
                metadata={
                    "employment_type": item.get("job_type") or "",
                },
            )
        )

    return jobs