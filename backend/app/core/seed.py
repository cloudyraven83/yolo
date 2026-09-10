"""初始化种子数据：管理员账号 + 商品/货道（读取 configs/drinks.yaml）。"""

import yaml

from .config import DRINKS_CONFIG
from .db import SessionLocal
from .security import hash_password
from ..models import AdminUser, Lane, Product

DEFAULT_ADMIN = ("admin", "admin123")


def load_drinks_config() -> dict:
    with open(DRINKS_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def auto_seed() -> dict:
    db = SessionLocal()
    created = {"admin": False, "products": 0, "lanes": 0}
    try:
        if db.query(AdminUser).count() == 0:
            db.add(AdminUser(username=DEFAULT_ADMIN[0],
                             password_hash=hash_password(DEFAULT_ADMIN[1])))
            created["admin"] = True

        if db.query(Product).count() == 0:
            cfg = load_drinks_config()
            for item in cfg.get("products", []):
                p = Product(
                    name=item["name"],
                    brand=item.get("brand", ""),
                    price=float(item["price"]),
                    unit=item.get("unit", "瓶"),
                )
                db.add(p)
                db.flush()
                db.add(Lane(
                    shelf_no=item.get("lane", f"L{p.id}"),
                    product_id=p.id,
                    capacity=int(item.get("capacity", 10)),
                    stock=int(item.get("stock", 0)),
                    threshold=int(item.get("threshold", 2)),
                ))
                created["products"] += 1
                created["lanes"] += 1
        db.commit()
    finally:
        db.close()
    return created
