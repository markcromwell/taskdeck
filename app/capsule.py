"""Capsule descriptor (+capsule module) — makes this program agent-addressable by construction (v2 §3).
charter = identity/mission/rules; skills = doc refs; tool_surface = the program's own endpoints, derived
MECHANICALLY from the FastAPI routes so it cannot drift from reality (no AI narrative here)."""
from __future__ import annotations

from typing import Any

CHARTER = {
    "name": "TaskDeck",
    "mission": "TODO: one sentence on what this program is for.",
    "rules": ["TODO: operating rules / non-goals"],
}

SKILLS: list[str] = []  # refs to skill docs this program relies on


def tool_surface(app) -> list[dict[str, Any]]:
    surface = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = sorted(getattr(route, "methods", None) or [])
        if not path or not methods or path in ("/openapi.json", "/docs", "/redoc"):
            continue
        surface.append({"path": path, "methods": [m for m in methods if m != "HEAD"]})
    return surface


def capsule(app) -> dict[str, Any]:
    return {"charter": CHARTER, "skills": SKILLS, "tool_surface": tool_surface(app)}
