from unittest.mock import Mock, patch

from src.collectors.greenhouse import collect_greenhouse
from src.main import collect_all
from src.models import Job
from src.scoring import score_job


def test_greenhouse_maps_public_post_and_skips_prospect():
    response = Mock()
    response.json.return_value = {
        "jobs": [
            {
                "id": 42,
                "internal_job_id": 123,
                "title": "Data Analyst",
                "location": {"name": "Remote - United States"},
                "absolute_url": "https://job-boards.greenhouse.io/example/jobs/42",
                "content": "&lt;p&gt;Python &amp;amp; SQL&lt;/p&gt;",
                "departments": [{"name": "Data"}],
            },
            {
                "id": 43,
                "internal_job_id": None,
                "title": "General interest",
                "location": {"name": "Remote - United States"},
                "absolute_url": "https://job-boards.greenhouse.io/example/jobs/43",
            },
        ]
    }
    with patch("src.collectors.greenhouse.requests.get", return_value=response) as get:
        jobs = collect_greenhouse("Example", "example")

    assert len(jobs) == 1
    assert jobs[0].job_id == "greenhouse:example:42"
    assert jobs[0].description == "Python & SQL"
    assert jobs[0].metadata["department"] == "Data"
    assert get.call_args.kwargs["params"] == {"content": "true"}


def test_collect_all_includes_greenhouse_board():
    example = Job(
        job_id="greenhouse:example:42",
        title="Data Analyst",
        company="Example",
        location="Remote - United States",
        url="https://job-boards.greenhouse.io/example/jobs/42",
        source="Greenhouse",
    )
    with patch("src.main.collect_greenhouse", return_value=[example]) as collect:
        assert collect_all({"sources": {"greenhouse": [{"company": "Example", "board": "example"}]}}) == [example]
    collect.assert_called_once_with("Example", "example")


def test_us_location_term_does_not_match_australia():
    config = {
        "require_remote": True,
        "allowed_location_terms": ["us", "united states"],
        "categories": {"data": {"title_terms": ["data analyst"]}},
    }
    job = Job(
        job_id="greenhouse:example:44",
        title="Data Analyst",
        company="Example",
        location="Australia - Remote",
        url="https://job-boards.greenhouse.io/example/jobs/44",
        source="Greenhouse",
        description="US customers",
    )
    assert score_job(job, config) is None
