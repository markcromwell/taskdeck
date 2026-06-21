"""Capsule + self-knowledge endpoints (+capsule module).
/capsule           — the agent capsule descriptor (charter + skills + tool_surface). Public.
/memory/salient    — what this program CONTAINS that matters, computed READ-THROUGH so it never goes stale.
/memory/important  — alias kept for the agent-readiness contract.
The /memory/* endpoints expose the most sensitive data, so they REQUIRE a token (CoEv2 must-fix #7)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request

router = APIRouter(tags=["capsule"])


def require_salient_token(x_salient_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("SALIENT_API_KEY", "")
    if not expected or x_salient_token != expected:
        raise HTTPException(status_code=401, detail="self-knowledge endpoints require a valid token")


@router.get("/capsule")
def get_capsule(request: Request):
    from app.capsule import capsule
    return capsule(request.app)


def salient_items() -> list[dict]:
    # READ-THROUGH: compute the salient slice live from current data so it never goes stale.
    # Replace this stub with a query curated by your salience schema.
    return []


@router.get("/memory/salient", dependencies=[Depends(require_salient_token)])
def memory_salient():
    return {"salient": salient_items()}


@router.get("/memory/important", dependencies=[Depends(require_salient_token)])
def memory_important():
    return {"important": salient_items()}
