"""Projects CRUD — authenticated via the shared app.auth.require_api_key (enforced when APP_API_KEY set)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_session
from app.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


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