"""Web UI (+ui module). Server-rendered Jinja page at /."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_session
from app.routers.projects import fetch_all_projects

router = APIRouter(tags=["web"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
_templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    projects = fetch_all_projects(session)
    return _templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "app_name": "TaskDeck", "projects": projects},
    )
