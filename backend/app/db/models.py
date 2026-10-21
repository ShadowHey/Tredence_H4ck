from datetime import datetime, timezone
from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    """Returns timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, default="General")
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="INR")
    width_cm = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)
    depth_cm = Column(Float, nullable=False)
    image_path = Column(String(500), nullable=False)
    is_sample = Column(Boolean, default=False, nullable=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    placements = relationship("Placement", back_populates="product", passive_deletes="all")

    __table_args__ = (
        CheckConstraint("width_cm > 0", name="check_product_width_positive"),
        CheckConstraint("height_cm > 0", name="check_product_height_positive"),
        CheckConstraint("depth_cm > 0", name="check_product_depth_positive"),
        CheckConstraint("price >= 0", name="check_product_price_non_negative"),
    )


class Planogram(Base):
    __tablename__ = "planograms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    shelves = relationship("Shelf", back_populates="planogram", cascade="all, delete-orphan", order_by="Shelf.order_index")


class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True)
    planogram_id = Column(Integer, ForeignKey("planograms.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="Shelf 01")
    width_cm = Column(Float, nullable=False, default=120.0)
    total_height_cm = Column(Float, nullable=False, default=180.0)
    depth_cm = Column(Float, nullable=False, default=40.0)
    row_count = Column(Integer, nullable=False, default=4)
    has_plinth = Column(Boolean, default=False, nullable=False)
    plinth_height_cm = Column(Float, default=0.0, nullable=False)
    row_heights = Column(JSON, nullable=True, default=None)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    planogram = relationship("Planogram", back_populates="shelves")
    placements = relationship("Placement", back_populates="shelf", cascade="all, delete-orphan", order_by="Placement.x_offset_cm")

    __table_args__ = (
        CheckConstraint("width_cm > 0", name="check_shelf_width_positive"),
        CheckConstraint("total_height_cm > 0", name="check_shelf_height_positive"),
        CheckConstraint("depth_cm > 0", name="check_shelf_depth_positive"),
        CheckConstraint("row_count >= 1 AND row_count <= 12", name="check_shelf_row_count_valid"),
        CheckConstraint("plinth_height_cm >= 0", name="check_shelf_plinth_non_negative"),
    )


class Placement(Base):
    __tablename__ = "placements"

    id = Column(Integer, primary_key=True, index=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)  # 0 to row_count - 1
    x_offset_cm = Column(Float, nullable=False, default=0.0)  # position from left edge of row in cm
    facing_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    shelf = relationship("Shelf", back_populates="placements")
    product = relationship("Product", back_populates="placements")

    __table_args__ = (
        CheckConstraint("row_index >= 0", name="check_placement_row_non_negative"),
        CheckConstraint("x_offset_cm >= 0", name="check_placement_x_non_negative"),
        CheckConstraint("facing_count >= 1", name="check_placement_facing_positive"),
    )
