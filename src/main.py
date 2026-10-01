from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from src.collectors.ashby import collect_ashby
from src.collectors.greenhouse import collect_greenhouse
from src.collectors.himalayas import collect_himalayas
from src.collectors.lever import collect_lever
from src.discord_client import post_jobs
from src.scoring import ScoredJob, score_job
from src.state import load_seen, save_seen


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "search.yaml"
STATE_PATH = ROOT / "data" / "seen_jobs.json"


def _match_key(job) -> str:
    # Keep a source-independent key so a later feed cannot repost the same role.
    company = re.sub(r"[^a-z0-9]+", "", job.company.casefold())
    title = re.sub(r"[^a-z0-9]+", "", job.title.casefold())
    return f"match:{company}:{title}"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def collect_all(config: dict):
    sources = config.get("sources") or {}
    jobs = []

    for source in sources.get("lever") or []:
        try:
            jobs.extend(collect_lever(source["company"], source["site"]))
        except Exception as exc:
            print(f"[WARN] Lever collection failed for {source}: {exc}")

    for source in sources.get("ashby") or []:
        try:
            jobs.extend(collect_ashby(source["company"], source["board"]))
        except Exception as exc:
            print(f"[WARN] Ashby collection failed for {source}: {exc}")

    for source in sources.get("greenhouse") or []:
        try:
            jobs.extend(collect_greenhouse(source["company"], source["board"]))
        except Exception as exc:
            print(f"[WARN] Greenhouse collection failed for {source}: {exc}")

    himalayas = sources.get("himalayas") or {}
    if himalayas.get("queries"):
        try:
            direct_roles = {_match_key(job) for job in jobs}
            for job in collect_himalayas(
                himalayas["queries"],
                max_pages=int(himalayas.get("max_pages", 2)),
                max_age_days=int(himalayas.get("max_age_days", 14)),
            ):
                if _match_key(job) not in direct_roles:
                    jobs.append(job)
        except Exception as exc:
            print(f"[WARN] Himalayas collection failed: {exc}")

    # Deduplicate within this run by canonical job_id.
    return list({job.job_id: job for job in jobs}.values())


def rank_new_jobs(jobs, config: dict, seen: set[str]) -> list[ScoredJob]:
    search_config = config.get("search") or {}
    ranked = []

    for job in jobs:
        if job.job_id in seen or _match_key(job) in seen:
            continue
        result = score_job(job, search_config)
        if result:
            ranked.append(result)

    ranked.sort(key=lambda item: (-item.score, item.job.company.lower(), item.job.title.lower()))
    limit = int(search_config.get("max_jobs_per_run", 20))
    return ranked[:limit]


def dry_run(items: list[ScoredJob]) -> None:
    if not items:
        print("No new matching jobs found.")
        return

    print(f"{len(items)} new matching jobs:")
    for item in items:
        job = item.job
        print(
            f"[{item.score:>2}] {job.title} | {job.company} | "
            f"{job.location or 'Unknown'} | {job.url}"
        )


def main() -> None:
    config = load_config()
    jobs = collect_all(config)
    seen = load_seen(STATE_PATH)
    ranked = rank_new_jobs(jobs, config, seen)

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("[INFO] DISCORD_WEBHOOK_URL is not set; running in dry-run mode.")
        dry_run(ranked)
        return

    if not ranked:
        print("No new matching jobs found.")
        return

    categories = (
        config.get("search", {})
        .get("categories", {})
    )

    category_labels = {
        category_name: category_config.get(
            "label",
            category_name.replace("_", " ").title(),
        )
        for category_name, category_config
        in categories.items()
    }

    post_jobs(
        webhook_url,
        ranked,
        category_labels,
    )

    for item in ranked:
        seen.add(item.job.job_id)
        seen.add(_match_key(item.job))
    save_seen(STATE_PATH, seen)
    print(f"Posted {len(ranked)} new jobs to Discord.")


if __name__ == "__main__":
    main()
