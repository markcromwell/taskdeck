"""Projects CRUD — authenticated when TASKDECK_API_KEY is configured."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("TASKDECK_API_KEY", "")
    if not expected:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="valid X-API-Key required")


class ProjectIn(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


def fetch_all_projects(session: Session) -> list[Project]:
    return session.query(Project).order_by(Project.id).all()


@router.get("", response_model=list[ProjectOut], dependencies=[Depends(require_api_key)])
def list_projects(session: Session = Depends(get_session)):
    return fetch_all_projects(session)


@router.post("", response_model=ProjectOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_project(payload: ProjectIn, session: Session = Depends(get_session)):
    project = Project(name=payload.name)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project