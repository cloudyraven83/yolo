"""会话状态机 + 关门结算 + 库存扣减 + 补货预警。"""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.runtime import runtime
from ..models import Alert, Lane, Product, RecognitionLog, SessionItem, VendingSession


def current_state(db: Session) -> dict:
    if runtime.session_id is not None:
        return {"state": "open", "session_id": runtime.session_id}
    latest = (
        db.query(VendingSession)
        .filter(VendingSession.status == "closed")
        .order_by(VendingSession.id.desc())
        .first()
    )
    if latest:
        return {"state": "closed", "session_id": latest.id}
    return {"state": "idle", "session_id": None}


def start_session(db: Session) -> VendingSession:
    with runtime.lock:
        if runtime.session_id is not None:
            raise HTTPException(400, "已有进行中的识别会话，请先关门结算")
        s = VendingSession(status="open")
        db.add(s)
        db.commit()
        db.refresh(s)
        runtime.session_id = s.id
        return s


def inject_scenario(db: Session, items: list) -> int:
    """演示场景注入：每件商品写一条 counted 识别日志。"""
    if runtime.session_id is None:
        raise HTTPException(400, "请先开始识别（开门）后再注入场景")
    count = 0
    for it in items:
        pid = it.get("product_id")
        qty = int(it.get("qty", 0))
        product = db.get(Product, pid) if pid else None
        if product is None or qty <= 0:
            continue
        for _ in range(qty):
            db.add(RecognitionLog(
                session_id=runtime.session_id,
                provider=runtime.provider_name,
                label=product.name,
                confidence=0.99,
                region="",
                counted=True,
            ))
            count += 1
    db.commit()
    return count


def _open_alert_exists(db: Session, lane_id: int) -> bool:
    return (
        db.query(Alert)
        .filter(Alert.lane_id == lane_id, Alert.status == "open")
        .first()
        is not None
    )


def stop_session(db: Session) -> dict:
    """关门：汇总净拿走量 -> 结算单 -> 扣库存 -> 低库存预警。"""
    with runtime.lock:
        sid = runtime.session_id
        if sid is None:
            raise HTTPException(400, "当前没有进行中的识别会话")
        s = db.get(VendingSession, sid)
        if s is None or s.status != "open":
            runtime.session_id = None
            raise HTTPException(400, "会话状态异常")

        logs = (
            db.query(RecognitionLog)
            .filter(RecognitionLog.session_id == sid, RecognitionLog.counted.is_(True))
            .all()
        )
        qty_by_label = {}
        for log in logs:
            qty_by_label[log.label] = qty_by_label.get(log.label, 0) + 1

        items, total, warnings = [], 0.0, []
        for label, qty in qty_by_label.items():
            product = db.query(Product).filter(Product.name == label).first()
            if product is None:
                warnings.append(f"未找到商品[{label}]，已忽略")
                continue
            lane = db.query(Lane).filter(Lane.product_id == product.id).first()
            if lane is None:
                warnings.append(f"商品[{label}]未配置货道，已忽略")
                continue
            if qty > lane.stock:  # 负库存保护：按实际库存结算
                warnings.append(
                    f"[{product.name}]拿走 {qty} 件但库存仅 {lane.stock} 件，按实际库存结算"
                )
                qty = lane.stock
            if qty <= 0:
                continue
            subtotal = round(qty * product.price, 2)
            db.add(SessionItem(
                session_id=sid, product_id=product.id, quantity=qty,
                unit_price=product.price, subtotal=subtotal,
            ))
            total += subtotal
            lane.stock -= qty
            if lane.stock < lane.threshold and not _open_alert_exists(db, lane.id):
                db.add(Alert(
                    lane_id=lane.id,
                    type="empty" if lane.stock == 0 else "low_stock",
                    message=(
                        f"货道 {lane.shelf_no}[{product.name}] "
                        + ("已售空，请立即补货" if lane.stock == 0
                           else f"库存 {lane.stock} 低于阈值 {lane.threshold}，请补货")
                    ),
                ))
            items.append({
                "product_id": product.id, "name": product.name,
                "quantity": qty, "unit_price": product.price, "subtotal": subtotal,
            })

        s.status = "closed"
        s.ended_at = datetime.now()
        s.total_amount = round(total, 2)
        runtime.session_id = None
        db.commit()
        return {
            "session_id": sid,
            "status": s.status,
            "items": items,
            "total_amount": s.total_amount,
            "warnings": warnings,
        }


def pay_session(db: Session, session_id: int) -> dict:
    s = db.get(VendingSession, session_id)
    if s is None:
        raise HTTPException(404, "会话不存在")
    if s.status == "paid":
        return {"session_id": s.id, "status": "paid"}
    if s.status != "closed":
        raise HTTPException(400, "会话尚未关门结算，无法支付")
    s.status = "paid"
    s.paid_at = datetime.now()
    db.commit()
    return {"session_id": s.id, "status": "paid", "paid_at": str(s.paid_at)}
