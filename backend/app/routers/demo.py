from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..services import session_service

router = APIRouter(prefix="/api/demo", tags=["demo"])


class ScenarioItem(BaseModel):
    product_id: int
    qty: int


class Scenario(BaseModel):
    items: list[ScenarioItem]


@router.post("/scenario")
def scenario(body: Scenario, db: Session = Depends(get_db)):
    count = session_service.inject_scenario(db, [i.model_dump() for i in body.items])
    return {"injected_events": count}
