import pytest

from src.main import load_config
from src.models import Job
from src.scoring import score_job


CONFIG = {
    "require_remote": True,
    "minimum_score": 5,

    "allowed_location_terms": [
        "us",
        "u.s.",
        "usa",
        "united states",
    ],

    "categories": {
        "project_management": {
            "label": "Project / Program Management",
            "title_terms": [
                "project manager",
                "program manager",
                "technical project manager",
                "technical program manager",
            ],
        },

        "data": {
            "label": "Data & Analytics",
            "title_terms": [
                "data analyst",
                "data engineer",
            ],
        },
    },

    "excluded_title_terms": [
        "sales",
    ],

    "excluded_location_terms": [
        "canada",
        "emea",
    ],

    "weights": {
        "project manager": 5,
        "llm": 4,
        "evaluation": 5,
        "python": 3,
    },
}


def test_remote_ai_project_manager_scores():
    job = Job(
        job_id="1",
        title="AI Project Manager",
        company="Example",
        location="Remote - United States",
        url="https://example.com/job/1",
        source="test",
        description="LLM evaluation workflows and Python.",
    )
    result = score_job(job, CONFIG)
    assert result is not None
    assert result.score >= 14
    assert "project_management" in result.categories


def test_non_remote_job_is_filtered():
    job = Job(
        job_id="2",
        title="Project Manager",
        company="Example",
        location="New York, NY",
        url="https://example.com/job/2",
        source="test",
        description="LLM evaluation workflows.",
    )
    assert score_job(job, CONFIG) is None


def test_excluded_location_is_filtered():
    job = Job(
        job_id="3",
        title="Data Analyst",
        company="Example",
        location="Remote - Canada",
        url="https://example.com/job/3",
        source="test",
        description="Python and evaluation.",
    )
    assert score_job(job, CONFIG) is None


@pytest.mark.parametrize("title", [
    "AI Operations Specialist",
    "AI Data Operations Manager",
    "Operations Lead, Artificial Intelligence",
    "AI/ML Ops Lead",
    "Data Annotator",
    "Annotation Quality Analyst",
    "Data Labelling Team Lead",
    "LLM Trainer",
    "AI Training Data Specialist",
    "AI Lead",
    "Lead AI Engineer",
    "AI Engineering Lead",
    "Head of Generative AI",
])
def test_ai_operations_titles_qualify_without_description_keywords(title):
    config = load_config()["search"]
    job = Job(
        job_id="1",
        title=title,
        company="Example",
        location="Remote - United States",
        url="https://example.com/1",
        source="test",
    )

    result = score_job(job, config)

    assert result is not None
    assert "ai_operations" in result.categories
    assert result.score >= config["minimum_score"]


@pytest.mark.parametrize("title", [
    "AI Lead Generation Specialist",
    "AIOps Specialist",
    "OpenAI Lead Generation Specialist",
    "Sales Coordinator",
])
def test_ai_operations_category_requires_a_relevant_title(title):
    config = load_config()["search"]
    job = Job(
        job_id="1",
        title=title,
        company="Example",
        location="Remote - United States",
        url="https://example.com/1",
        source="test",
        description="Support AI operations, LLM evaluation, and data annotation teams.",
    )

    assert score_job(job, config) is None


@pytest.mark.parametrize("location", ["United States", "Remote - Canada"])
def test_ai_operations_titles_still_require_an_eligible_remote_location(location):
    config = load_config()["search"]
    job = Job(
        job_id="1",
        title="AI Operations Lead",
        company="Example",
        location=location,
        url="https://example.com/1",
        source="test",
    )

    assert score_job(job, config) is None
