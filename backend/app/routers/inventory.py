from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_admin
from ..models import AdminUser, Alert, Lane, Product, RestockOrder

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """公开接口：操作台演示场景选择用。"""
    return [
        {"id": p.id, "name": p.name, "brand": p.brand, "price": p.price, "unit": p.unit}
        for p in db.query(Product).order_by(Product.id).all()
    ]


@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    rows = (
        db.query(Lane, Product)
        .join(Product, Product.id == Lane.product_id)
        .order_by(Lane.shelf_no)
        .all()
    )
    return [
        {
            "lane_id": lane.id,
            "shelf_no": lane.shelf_no,
            "product_id": p.id,
            "name": p.name,
            "brand": p.brand,
            "price": p.price,
            "capacity": lane.capacity,
            "stock": lane.stock,
            "threshold": lane.threshold,
            "low_stock": lane.stock < lane.threshold,
        }
        for lane, p in rows
    ]


class LaneUpdate(BaseModel):
    price: float | None = None
    threshold: int | None = None
    capacity: int | None = None


@router.put("/inventory/lane/{lane_id}")
def update_lane(lane_id: int, body: LaneUpdate, db: Session = Depends(get_db),
                _: AdminUser = Depends(get_current_admin)):
    lane = db.get(Lane, lane_id)
    if lane is None:
        raise HTTPException(404, "货道不存在")
    if body.threshold is not None:
        lane.threshold = max(0, int(body.threshold))
    if body.capacity is not None:
        lane.capacity = max(0, int(body.capacity))
    if body.price is not None:
        product = db.get(Product, lane.product_id)
        product.price = round(float(body.price), 2)
    db.commit()
    return {"ok": True}


class RestockBody(BaseModel):
    lane_id: int
    quantity: int


@router.post("/restock")
def restock(body: RestockBody, db: Session = Depends(get_db),
            admin: AdminUser = Depends(get_current_admin)):
    lane = db.get(Lane, body.lane_id)
    if lane is None:
        raise HTTPException(404, "货道不存在")
    qty = int(body.quantity)
    if qty <= 0:
        raise HTTPException(400, "补货数量必须大于 0")
    lane.stock = min(lane.capacity, lane.stock + qty)
    db.add(RestockOrder(
        lane_id=lane.id, product_id=lane.product_id,
        quantity=qty, operator=admin.username,
    ))
    # 库存恢复到阈值以上则自动关闭该货道的未处理预警
    if lane.stock >= lane.threshold:
        for a in db.query(Alert).filter(
                Alert.lane_id == lane.id, Alert.status == "open").all():
            a.status = "resolved"
            a.resolved_at = datetime.now()
    db.commit()
    return {"ok": True, "stock": lane.stock}
