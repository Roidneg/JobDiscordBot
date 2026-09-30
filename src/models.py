from dataclasses import dataclass, field


@dataclass(frozen=True)
class Job:
    job_id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    compensation: str = ""
    metadata: dict = field(default_factory=dict, compare=False, hash=False)
