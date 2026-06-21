# Unit tests for TaskDeck. Uses the app factory for an isolated instance.
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app

client = TestClient(create_app())

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"

REQUIRED_ARCHITECTURE_SECTIONS = (
    "Project Overview",
    "File Structure",
    "Naming Conventions",
    "Module Responsibilities",
    "How to Test",
)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_architecture_contract():
    assert ARCHITECTURE_MD.is_file(), "ARCHITECTURE.md must exist at repo root"
    content = ARCHITECTURE_MD.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert len(lines) <= 150, f"ARCHITECTURE.md must be <=150 lines, got {len(lines)}"
    for section in REQUIRED_ARCHITECTURE_SECTIONS:
        assert section in content, f"ARCHITECTURE.md missing section: {section}"
