from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_admin
from ..models import (AdminUser, Alert, Lane, Product, RecognitionLog,
                      SessionItem, VendingSession)

router = APIRouter(prefix="/api", tags=["records"],
                   dependencies=[Depends(get_current_admin)])


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    rows = (
        db.query(Alert, Lane, Product)
        .join(Lane, Lane.id == Alert.lane_id)
        .join(Product, Product.id == Lane.product_id)
        .order_by(Alert.id.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": a.id, "lane_id": a.lane_id, "shelf_no": lane.shelf_no,
            "product": p.name, "type": a.type, "status": a.status,
            "message": a.message, "created_at": str(a.created_at),
            "resolved_at": str(a.resolved_at) if a.resolved_at else None,
        }
        for a, lane, p in rows
    ]


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(404, "预警不存在")
    a.status = "resolved"
    a.resolved_at = datetime.now()
    db.commit()
    return {"ok": True}


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    rows = db.query(VendingSession).order_by(VendingSession.id.desc()).limit(50).all()
    return [
        {
            "id": s.id, "started_at": str(s.started_at),
            "ended_at": str(s.ended_at) if s.ended_at else None,
            "status": s.status, "total_amount": s.total_amount,
            "paid_at": str(s.paid_at) if s.paid_at else None,
        }
        for s in rows
    ]


@router.get("/sessions/{session_id}")
def session_detail(session_id: int, db: Session = Depends(get_db)):
    s = db.get(VendingSession, session_id)
    if s is None:
        raise HTTPException(404, "会话不存在")
    items = (
        db.query(SessionItem, Product)
        .join(Product, Product.id == SessionItem.product_id)
        .filter(SessionItem.session_id == session_id)
        .all()
    )
    logs = (
        db.query(RecognitionLog)
        .filter(RecognitionLog.session_id == session_id)
        .order_by(RecognitionLog.id)
        .limit(200)
        .all()
    )
    return {
        "id": s.id, "status": s.status, "started_at": str(s.started_at),
        "ended_at": str(s.ended_at) if s.ended_at else None,
        "total_amount": s.total_amount,
        "paid_at": str(s.paid_at) if s.paid_at else None,
        "items": [
            {"name": p.name, "quantity": it.quantity,
             "unit_price": it.unit_price, "subtotal": it.subtotal}
            for it, p in items
        ],
        "logs": [
            {"ts": str(l.ts), "provider": l.provider, "label": l.label,
             "confidence": l.confidence, "counted": l.counted}
            for l in logs
        ],
    }
