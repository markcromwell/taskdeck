"""Items CRUD (+db module example surface). Replace with real business endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Item

router = APIRouter(prefix="/items", tags=["items"])


class ItemIn(BaseModel):
    name: str


class ItemOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


@router.get("", response_model=list[ItemOut])
def list_items(session: Session = Depends(get_session)):
    return session.query(Item).order_by(Item.id).all()


@router.post("", response_model=ItemOut, status_code=201)
def create_item(payload: ItemIn, session: Session = Depends(get_session)):
    item = Item(name=payload.name)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
