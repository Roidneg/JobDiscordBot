from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.collectors.himalayas import collect_himalayas
from src.discord_client import _embed
from src.main import _match_key, collect_all, rank_new_jobs
from src.models import Job
from src.scoring import ScoredJob


def _listing(**overrides):
    item = {
        "title": "Technical Program Manager",
        "companyName": "Example AI",
        "guid": "https://himalayas.app/companies/example/jobs/tpm",
        "applicationLink": "https://himalayas.app/companies/example/jobs/tpm",
        "locationRestrictions": ["United States"],
        "timezoneRestrictions": [-6, -5],
        "description": "<p>LLM &amp; Python</p>",
        "pubDate": int(datetime.now(timezone.utc).timestamp()),
        "expiryDate": int((datetime.now(timezone.utc) + timedelta(days=10)).timestamp()),
        "minSalary": 150000,
        "maxSalary": 200000,
        "currency": "USD",
        "salaryPeriod": "annual",
    }
    item.update(overrides)
    return item


def test_himalayas_maps_eligible_recent_jobs_and_credits_source():
    response = Mock()
    response.json.return_value = {"jobs": [
        _listing(),
        _listing(guid="canada", locationRestrictions=["Canada"]),
        _listing(guid="timezone", locationRestrictions=[], timezoneRestrictions=[2]),
        _listing(guid="old", pubDate=1),
        _listing(guid="expired", expiryDate=1),
        _listing(guid="worldwide", locationRestrictions=[], timezoneRestrictions=[]),
    ]}
    with patch("src.collectors.himalayas.requests.get", return_value=response) as get:
        jobs = collect_himalayas(["program manager"], max_pages=2)

    assert len(jobs) == 2
    assert jobs[0].job_id.startswith("himalayas:")
    assert jobs[0].description == "LLM & Python"
    assert jobs[0].compensation == "USD 150,000–200,000 / annual"
    assert jobs[1].location == "Remote - Worldwide (US eligible)"
    assert get.call_count == 1
    assert get.call_args.kwargs["params"] == {
        "q": "program manager", "country": "US", "sort": "recent", "page": 1,
    }

    embed = _embed(ScoredJob(jobs[0], 5, (), ("project_management",)), {})
    assert embed["url"] == jobs[0].url
    assert embed["footer"]["text"] == "Source: Himalayas"


def test_himalayas_paginates_and_deduplicates_across_queries():
    first = Mock()
    first.json.return_value = {"jobs": [_listing()] * 20}
    second = Mock()
    second.json.return_value = {"jobs": [_listing(), _listing(guid="other")]}
    with patch("src.collectors.himalayas.requests.get", side_effect=[first, second, second]) as get:
        jobs = collect_himalayas(["program manager", "technical program manager"])

    assert len(jobs) == 2
    assert get.call_count == 3
    assert get.call_args_list[1].kwargs["params"]["page"] == 2


def test_rate_limit_keeps_results_from_completed_searches():
    first = Mock(status_code=200)
    first.json.return_value = {"jobs": [_listing()]}
    limited = Mock(status_code=429)
    with patch("src.collectors.himalayas.requests.get", side_effect=[first, limited]):
        jobs = collect_himalayas(["program manager", "data analyst"])
    assert len(jobs) == 1


def test_direct_board_job_wins_and_cross_run_key_prevents_repost():
    direct = Job(
        job_id="ashby:example:123", title="Technical Program Manager", company="Example AI",
        location="Remote - United States", url="https://jobs.ashbyhq.com/example/123",
        source="Ashby", description="LLM",
    )
    feed = Job(
        job_id="himalayas:example", title=direct.title, company=direct.company,
        location=direct.location, url="https://himalayas.app/companies/example/jobs/tpm",
        source="Himalayas", description="LLM",
    )
    config = {"sources": {
        "ashby": [{"company": "Example AI", "board": "example"}],
        "himalayas": {"queries": ["program manager"]},
    }}
    with patch("src.main.collect_ashby", return_value=[direct]), patch(
        "src.main.collect_himalayas", return_value=[feed]
    ):
        assert collect_all(config) == [direct]

    search = {"categories": {"project_management": {"title_terms": ["program manager"]}},
              "allowed_location_terms": ["united states"], "require_remote": True,
              "weights": {"program manager": 5}, "minimum_score": 5}
    assert rank_new_jobs([feed], {"search": search}, {_match_key(direct)}) == []
