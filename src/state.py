from __future__ import annotations

import json
from pathlib import Path


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()

    if isinstance(payload, list):
        return {str(item) for item in payload}
    return set()


def save_seen(path: Path, seen: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sorted(seen), indent=2) + "\n",
        encoding="utf-8",
    )
