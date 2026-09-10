from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.runtime import runtime
from ..services import session_service

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/current")
def current(db: Session = Depends(get_db)):
    state = session_service.current_state(db)
    state["provider"] = runtime.provider_name
    return state


@router.post("/start")
def start(db: Session = Depends(get_db)):
    s = session_service.start_session(db)
    return {"session_id": s.id, "status": s.status, "started_at": str(s.started_at)}


@router.post("/stop")
def stop(db: Session = Depends(get_db)):
    return session_service.stop_session(db)


@router.post("/{session_id}/pay")
def pay(session_id: int, db: Session = Depends(get_db)):
    return session_service.pay_session(db, session_id)
