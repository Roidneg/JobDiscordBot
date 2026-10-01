from __future__ import annotations

import html
import re
from datetime import datetime, timezone

import requests

from src.models import Job


BASE_URL = "https://himalayas.app/jobs/api/search"
US_NAMES = {"us", "usa", "united states", "united states of america"}
US_TIMEZONES = {-10, -9, -8, -7, -6, -5, -4}


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()


def _timestamp(value: object) -> float | None:
    if isinstance(value, (float, int)):
        return value / 1000 if value > 10**11 else float(value)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _country_name(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("alpha2") or value.get("name") or value.get("slug") or "")
    return str(value)


def _us_eligible(item: dict) -> bool:
    countries = item.get("locationRestrictions") or []
    if countries and not any(_country_name(country).casefold() in US_NAMES for country in countries):
        return False

    timezones = item.get("timezoneRestrictions") or []
    if timezones:
        try:
            return any(float(offset) in US_TIMEZONES for offset in timezones)
        except (ValueError, TypeError):
            return False
    return True


def _location(item: dict) -> str:
    countries = item.get("locationRestrictions") or []
    if not countries:
        return "Remote - Worldwide (US eligible)"
    names = [_country_name(country) for country in countries]
    if len(names) == 1:
        return f"Remote - {'United States' if names[0].casefold() in US_NAMES else names[0]}"
    return "Remote - United States and other countries"


def _compensation(item: dict) -> str:
    minimum, maximum = item.get("minSalary"), item.get("maxSalary")
    if minimum is None and maximum is None:
        return ""
    currency = item.get("currency") or ""
    period = item.get("salaryPeriod") or "annual"
    amounts = [f"{amount:,.0f}" for amount in (minimum, maximum) if amount is not None]
    return f"{currency} {'–'.join(amounts)} / {period}".strip()


def collect_himalayas(
    queries: list[str], max_pages: int = 2, max_age_days: int = 14, timeout: int = 20
) -> list[Job]:
    jobs: dict[str, Job] = {}
    now = datetime.now(timezone.utc).timestamp()

    for query in queries:
        for page in range(1, max_pages + 1):
            response = requests.get(
                BASE_URL,
                params={"q": query, "country": "US", "sort": "recent", "page": page},
                timeout=timeout,
                headers={"Accept": "application/json", "User-Agent": "discord-job-intelligence/0.1"},
            )
            if response.status_code == 429:
                print("[WARN] Himalayas rate limit reached; keeping jobs collected so far.")
                return list(jobs.values())
            response.raise_for_status()
            items = response.json().get("jobs") or []

            for item in items:
                if not _us_eligible(item):
                    continue
                published = _timestamp(item.get("pubDate"))
                expired = _timestamp(item.get("expiryDate"))
                if (published and now - published > max_age_days * 86400) or (expired and expired < now):
                    continue

                url = item.get("applicationLink") or ""
                identifier = item.get("guid") or url
                title = (item.get("title") or "").strip()
                company = (item.get("companyName") or "").strip()
                if not (url and identifier and title and company):
                    continue

                job_id = f"himalayas:{identifier}"
                jobs[job_id] = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=_location(item),
                    url=url,
                    source="Himalayas",
                    description=_plain_text(item.get("description") or item.get("excerpt") or ""),
                    compensation=_compensation(item),
                    metadata={"employment_type": item.get("employmentType") or ""},
                )

            if len(items) < 20:
                break

    return list(jobs.values())
