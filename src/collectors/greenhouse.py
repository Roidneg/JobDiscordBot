from __future__ import annotations

import html
import re

import requests

from src.models import Job


BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"


def _plain_text(value: str) -> str:
    # Greenhouse encodes HTML in the description, sometimes more than once.
    decoded = html.unescape(html.unescape(value or ""))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", decoded)).strip()


def collect_greenhouse(company: str, board: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(board=board),
        params={"content": "true"},
        timeout=timeout,
        headers={"Accept": "application/json", "User-Agent": "discord-job-intelligence/0.1"},
    )
    response.raise_for_status()

    jobs: list[Job] = []
    for item in response.json().get("jobs", []):
        posting_id = item.get("id")
        url = item.get("absolute_url") or ""
        if posting_id is None or not url or item.get("internal_job_id") is None:
            continue

        location = item.get("location") or {}
        departments = item.get("departments") or []
        jobs.append(
            Job(
                job_id=f"greenhouse:{board}:{posting_id}",
                title=(item.get("title") or "").strip(),
                company=company,
                location=(location.get("name") or "").strip(),
                url=url,
                source="Greenhouse",
                description=_plain_text(item.get("content") or ""),
                metadata={
                    "department": ", ".join(
                        department.get("name", "") for department in departments
                    ),
                },
            )
        )

    return jobs
