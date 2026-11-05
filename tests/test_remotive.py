from unittest.mock import patch

from src.collectors.remotive import collect_remotive


@patch("src.collectors.remotive.requests.get")
def test_collect_remotive_converts_listing(mock_get):
    mock_get.return_value.json.return_value = {
        "jobs": [
            {
                "id": 123,
                "title": "Freelance Copywriter",
                "company_name": "Example Company",
                "url": "https://remotive.com/remote-jobs/example-123",
                "candidate_required_location": "Worldwide",
                "description": "<p>A <strong>remote</strong> role.</p>",
                "salary": "$50,000",
                "job_type": "freelance",
            }
        ]
    }

    jobs = collect_remotive()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_id == "remotive:123"
    assert job.title == "Freelance Copywriter"
    assert job.source == "Remotive"
    assert job.url == "https://remotive.com/remote-jobs/example-123"
    assert job.description == "A remote role."
    assert job.location == "Remote - Worldwide (US eligibility not verified)"
    assert job.compensation == "$50,000"
    assert job.metadata["employment_type"] == "freelance"