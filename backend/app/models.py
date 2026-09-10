from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from .core.db import Base


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    brand = Column(String, default="")
    price = Column(Float, nullable=False, default=0.0)
    unit = Column(String, default="瓶")


class Lane(Base):
    __tablename__ = "lane"
    id = Column(Integer, primary_key=True)
    shelf_no = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    capacity = Column(Integer, default=10)
    stock = Column(Integer, default=0)
    threshold = Column(Integer, default=2)


class VendingSession(Base):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="open")  # open / closed(待支付) / paid
    total_amount = Column(Float, default=0.0)
    paid_at = Column(DateTime, nullable=True)


class SessionItem(Base):
    __tablename__ = "session_item"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)


class RecognitionLog(Base):
    __tablename__ = "recognition_log"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=True)
    ts = Column(DateTime, default=datetime.now)
    frame_no = Column(Integer, default=0)
    provider = Column(String, default="")
    label = Column(String, default="")
    confidence = Column(Float, default=0.0)
    region = Column(String, default="")
    counted = Column(Boolean, default=False)


class RestockOrder(Base):
    __tablename__ = "restock_order"
    id = Column(Integer, primary_key=True)
    lane_id = Column(Integer, ForeignKey("lane.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, default=0)
    operator = Column(String, default="")
    created_at = Column(DateTime, default=datetime.now)


class Alert(Base):
    __tablename__ = "alert"
    id = Column(Integer, primary_key=True)
    lane_id = Column(Integer, ForeignKey("lane.id"), nullable=False)
    type = Column(String, default="low_stock")  # low_stock / empty
    status = Column(String, default="open")  # open / resolved
    message = Column(String, default="")
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")
