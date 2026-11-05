from unittest.mock import patch

from src.main import collect_all, rank_new_jobs
from src.models import Job
from src.scoring import ScoredJob


def make_job(job_id: str, title: str) -> Job:
    return Job(
        job_id=job_id,
        title=title,
        company="Example",
        location="Remote - United States",
        url=f"https://example.com/{job_id}",
        source="test",
    )


def test_ranking_balances_categories_without_repeating_jobs():
    project_job = make_job("1", "Project Manager")
    shared_job = make_job("2", "AI Project Manager")
    art_job = make_job("3", "AI Artist")
    another_project_job = make_job("4", "Program Manager")

    scored = {
        "1": ScoredJob(project_job, 20, (), ("project_management",)),
        "2": ScoredJob(
            shared_job,
            15,
            (),
            ("project_management", "design_art"),
        ),
        "3": ScoredJob(art_job, 5, (), ("design_art",)),
        "4": ScoredJob(
            another_project_job,
            10,
            (),
            ("project_management",),
        ),
    }

    config = {
        "search": {
            "max_jobs_per_run": 4,
            "categories": {
                "project_management": {},
                "design_art": {},
            },
        }
    }

    jobs = [project_job, shared_job, art_job, another_project_job]

    with patch("src.main.score_job", side_effect=lambda job, _: scored[job.job_id]):
        result = rank_new_jobs(jobs, config, seen=set())

    selected_ids = [item.job.job_id for item in result]

    assert selected_ids == ["1", "2", "4", "3"]
    assert len(selected_ids) == len(set(selected_ids))


def test_small_digest_includes_different_categories():
    project_job = make_job("1", "Project Manager")
    another_project_job = make_job("2", "Program Manager")
    art_job = make_job("3", "AI Artist")

    scored = {
        "1": ScoredJob(project_job, 20, (), ("project_management",)),
        "2": ScoredJob(another_project_job, 15, (), ("project_management",)),
        "3": ScoredJob(art_job, 5, (), ("design_art",)),
    }

    config = {
        "search": {
            "max_jobs_per_run": 2,
            "categories": {
                "project_management": {},
                "design_art": {},
            },
        }
    }

    jobs = [project_job, another_project_job, art_job]

    with patch("src.main.score_job", side_effect=lambda job, _: scored[job.job_id]):
        result = rank_new_jobs(jobs, config, seen=set())

    assert [item.job.job_id for item in result] == ["1", "3"]

def test_collection_prefers_direct_listing_over_remotive_duplicate():
    direct_job = make_job("direct:1", "AI Artist")
    remotive_job = make_job("remotive:1", "AI Artist")

    config = {
        "sources": {
            "ashby": [
                {"company": "Example", "board": "example"},
            ],
            "remotive": {"enabled": True},
        }
    }

    with (
        patch("src.main.collect_ashby", return_value=[direct_job]),
        patch("src.main.collect_remotive", return_value=[remotive_job]),
    ):
        jobs = collect_all(config)

    assert len(jobs) == 1
    assert jobs[0].job_id == "direct:1"