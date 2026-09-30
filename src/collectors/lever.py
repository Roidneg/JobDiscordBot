from __future__ import annotations

import requests

from src.models import Job


BASE_URL = "https://api.lever.co/v0/postings/{site}"


def collect_lever(company: str, site: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(site=site),
        params={"mode": "json"},
        timeout=timeout,
        headers={"Accept": "application/json", "User-Agent": "discord-job-intelligence/0.1"},
    )
    response.raise_for_status()

    jobs: list[Job] = []
    for item in response.json():
        categories = item.get("categories") or {}
        location = categories.get("location") or item.get("workplaceType") or ""
        description = (
            item.get("descriptionPlain")
            or item.get("description")
            or item.get("additionalPlain")
            or ""
        )
        posting_id = str(item.get("id") or item.get("hostedUrl") or item.get("applyUrl"))
        url = item.get("hostedUrl") or item.get("applyUrl") or ""

        if not posting_id or not url:
            continue

        jobs.append(
            Job(
                job_id=f"lever:{site}:{posting_id}",
                title=(item.get("text") or "").strip(),
                company=company,
                location=str(location).strip(),
                url=url,
                source="Lever",
                description=str(description),
                metadata={
                    "team": categories.get("team", ""),
                    "commitment": categories.get("commitment", ""),
                    "workplace_type": item.get("workplaceType", ""),
                },
            )
        )

    return jobs
