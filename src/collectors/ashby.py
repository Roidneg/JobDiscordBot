from __future__ import annotations

import re

import requests

from src.models import Job


BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board}"


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "")


def collect_ashby(company: str, board: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(board=board),
        params={"includeCompensation": "true"},
        timeout=timeout,
        headers={"Accept": "application/json", "User-Agent": "discord-job-intelligence/0.1"},
    )
    response.raise_for_status()

    jobs: list[Job] = []
    for item in response.json().get("jobs", []):
        if item.get("isListed") is False:
            continue

        url = item.get("jobUrl") or item.get("applyUrl") or ""
        if not url:
            continue

        posting_id = str(item.get("id") or url)
        compensation = item.get("compensation") or {}
        comp_text = (
            compensation.get("scrapeableCompensationSalarySummary")
            or compensation.get("compensationTierSummary")
            or ""
        )

        description = (
            item.get("descriptionPlain")
            or _strip_html(item.get("descriptionHtml", ""))
            or ""
        )

        jobs.append(
            Job(
                job_id=f"ashby:{board}:{posting_id}",
                title=(item.get("title") or "").strip(),
                company=company,
                location=(item.get("location") or "").strip(),
                url=url,
                source="Ashby",
                description=description,
                compensation=str(comp_text).strip(),
                metadata={
                    "workplace_type": item.get("workplaceType", ""),
                    "department": item.get("department", ""),
                    "team": item.get("team", ""),
                },
            )
        )

    return jobs
