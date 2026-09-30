from __future__ import annotations

import requests

from src.scoring import ScoredJob


def _truncate(value: str, limit: int) -> str:
    value = value.strip()

    if len(value) <= limit:
        return value

    return value[: limit - 1].rstrip() + "…"


def _category_labels(
    item: ScoredJob,
    labels: dict[str, str],
) -> str:
    resolved = []

    for category in item.categories:
        label = labels.get(
            category,
            category.replace("_", " ").title(),
        )

        resolved.append(label)

    return "\n".join(resolved) or "Other"


def _embed(
    item: ScoredJob,
    category_labels: dict[str, str],
) -> dict:
    job = item.job

    fields = [
        {
            "name": "Category",
            "value": _category_labels(
                item,
                category_labels,
            ),
            "inline": True,
        },
        {
            "name": "Location",
            "value": job.location or "Not listed",
            "inline": True,
        },
    ]

    if job.compensation:
        fields.append(
            {
                "name": "Compensation",
                "value": _truncate(
                    job.compensation,
                    1024,
                ),
                "inline": False,
            }
        )

    if item.reasons:
        fields.append(
            {
                "name": "Matched On",
                "value": ", ".join(item.reasons),
                "inline": False,
            }
        )

    return {
        "title": _truncate(
            job.title,
            256,
        ),
        "url": job.url,
        "description": f"**{job.company}**",
        "fields": fields,
        "footer": {
            "text": f"Source: {job.source}"
        },
    }


def post_jobs(
    webhook_url: str,
    jobs: list[ScoredJob],
    category_labels: dict[str, str],
    timeout: int = 20,
) -> None:

    if not jobs:
        return

    total_jobs = len(jobs)

    for index in range(
        0,
        total_jobs,
        10,
    ):
        batch = jobs[index:index + 10]

        payload = {
            "username": "Remote Job Intelligence",
            "embeds": [
                _embed(
                    item,
                    category_labels,
                )
                for item in batch
            ],
            "allowed_mentions": {
                "parse": []
            },
        }

        if index == 0:
            payload["content"] = (
                "## Daily Remote Job Digest\n"
                f"**{total_jobs} new remote "
                f"opportunit"
                f"{'y' if total_jobs == 1 else 'ies'} found.**"
            )

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
        )

        response.raise_for_status()