"""运营统计：概览指标 / 近 N 天销售趋势 / 品类销售占比。"""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Product, RecognitionLog, SessionItem, VendingSession

SETTLED = ("closed", "paid")  # 已结算口径（含待支付与已支付）


def overview(db: Session) -> dict:
    row = (
        db.query(func.coalesce(func.sum(VendingSession.total_amount), 0.0),
                 func.count(VendingSession.id))
        .filter(VendingSession.status.in_(SETTLED))
        .one()
    )
    total_logs = db.query(func.count(RecognitionLog.id)).scalar() or 0
    counted_logs = (
        db.query(func.count(RecognitionLog.id))
        .filter(RecognitionLog.counted.is_(True))
        .scalar() or 0
    )
    # 演示期准确率口径：成交识别事件 / 全部识别事件（详见 task.md §5.5）
    accuracy = round(counted_logs / total_logs * 100, 1) if total_logs else None
    return {
        "total_sales": round(float(row[0]), 2),
        "total_orders": int(row[1]),
        "accuracy": accuracy,
    }


def trend(db: Session, days: int = 7) -> list:
    days = max(1, min(int(days), 90))
    today = datetime.now().date()
    start = datetime.combine(today - timedelta(days=days - 1), datetime.min.time())
    rows = (
        db.query(VendingSession.started_at, VendingSession.total_amount)
        .filter(VendingSession.status.in_(SETTLED),
                VendingSession.started_at >= start)
        .all()
    )
    bucket = {}
    for ts, amount in rows:
        key = ts.date().isoformat()
        bucket[key] = round(bucket.get(key, 0.0) + float(amount), 2)
    return [
        {"date": (today - timedelta(days=i)).isoformat(),
         "amount": bucket.get((today - timedelta(days=i)).isoformat(), 0.0)}
        for i in range(days - 1, -1, -1)
    ]


def category(db: Session) -> list:
    rows = (
        db.query(Product.name, func.coalesce(func.sum(SessionItem.quantity), 0))
        .join(SessionItem, SessionItem.product_id == Product.id)
        .join(VendingSession, VendingSession.id == SessionItem.session_id)
        .filter(VendingSession.status.in_(SETTLED))
        .group_by(Product.name)
        .all()
    )
    return [{"name": name, "value": int(qty)} for name, qty in rows]
