from src.discord_client import _embed
from src.models import Job
from src.scoring import ScoredJob


def make_item(metadata):
    job = Job(
        job_id="test",
        title="AI Artist",
        company="Example",
        location="Remote - United States",
        url="https://example.com",
        source="test",
        metadata=metadata,
    )
    return ScoredJob(
        job=job,
        score=5,
        reasons=(),
        categories=("design_art",),
    )


def test_embed_shows_employment_type_when_available():
    fields = _embed(make_item({"employment_type": "full_time"}), {})["fields"]

    assert {
        "name": "Employment type",
        "value": "Full Time",
        "inline": True,
    } in fields


def test_embed_omits_employment_type_when_missing():
    fields = _embed(make_item({}), {})["fields"]

    assert not any(field["name"] == "Employment type" for field in fields)