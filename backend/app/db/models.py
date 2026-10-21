from datetime import datetime
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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    shelf = relationship("Shelf", back_populates="placements")
    product = relationship("Product", back_populates="placements")

    __table_args__ = (
        CheckConstraint("row_index >= 0", name="check_placement_row_non_negative"),
        CheckConstraint("x_offset_cm >= 0", name="check_placement_x_non_negative"),
        CheckConstraint("facing_count >= 1", name="check_placement_facing_positive"),
    )


class InputImage(Base):
    """A shelf photograph staged for a single, explicitly selected shelf."""
    __tablename__ = "input_images"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="ready", index=True)
    planogram_id = Column(Integer, ForeignKey("planograms.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    planogram = relationship("Planogram")
    shelf = relationship("Shelf")
    job = relationship("ProcessingJob", back_populates="input_image", cascade="all, delete-orphan", uselist=False)
    output = relationship("ProcessedOutput", back_populates="input_image", cascade="all, delete-orphan", uselist=False)


class ProcessingJob(Base):
    """Durable, sequential image-processing work item."""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    input_image_id = Column(Integer, ForeignKey("input_images.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    input_image = relationship("InputImage", back_populates="job")
    output = relationship("ProcessedOutput", back_populates="job", cascade="all, delete-orphan", uselist=False)


class ProcessedOutput(Base):
    """Artifacts and metrics produced from one input image processing job."""
    __tablename__ = "processed_outputs"

    id = Column(Integer, primary_key=True, index=True)
    input_image_id = Column(Integer, ForeignKey("input_images.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    annotated_image_path = Column(String(500), nullable=False)
    result_json_path = Column(String(500), nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    input_image = relationship("InputImage", back_populates="output")
    job = relationship("ProcessingJob", back_populates="output")
