"""Unit tests for CLIP vector embeddings, L2 normalization, and identity similarity."""

from pathlib import Path
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Product
from app.services.embedding_service import ClipEmbeddingService, embedding_service


@pytest.fixture(scope="module")
def sample_image_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    path = repo_root / "sample_assets" / "images" / "crispy_chips_bag.png"
    assert path.is_file(), f"Sample image not found: {path}"
    return path


@pytest.fixture(scope="module")
def cleaner_image_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    path = repo_root / "sample_assets" / "images" / "cleaner_spray.png"
    assert path.is_file(), f"Cleaner image not found: {path}"
    return path


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_embedding_dimension_and_l2_norm(sample_image_path: Path):
    """Verify that CLIP embedding output has exactly 512 dimensions and unit L2 norm."""
    vec = embedding_service.compute_image_embedding(sample_image_path)
    assert isinstance(vec, list)
    assert len(vec) == 512

    # L2 norm must be 1.0
    l2_norm = sum(x * x for x in vec) ** 0.5
    assert pytest.approx(l2_norm, abs=1e-4) == 1.0


def test_identical_image_identity(sample_image_path: Path):
    """Verify that feeding an identical copy of an image produces cosine similarity == 1.0000."""
    # Compute from path
    vec1 = embedding_service.compute_image_embedding(sample_image_path)
    # Compute from freshly opened PIL Image copy
    img_copy = Image.open(sample_image_path).copy()
    vec2 = embedding_service.compute_image_embedding(img_copy)

    sim = embedding_service.cosine_similarity(vec1, vec2)
    assert pytest.approx(sim, abs=1e-4) == 1.0
    assert sim >= 0.9999


def test_cross_category_distinctness(sample_image_path: Path, cleaner_image_path: Path):
    """Verify that distinct product categories (chips vs cleaner spray) have noticeably lower similarity."""
    chips_vec = embedding_service.compute_image_embedding(sample_image_path)
    cleaner_vec = embedding_service.compute_image_embedding(cleaner_image_path)

    sim = embedding_service.cosine_similarity(chips_vec, cleaner_vec)
    # Chips and cleaning spray should not be identical
    assert sim < 0.85
    assert sim > -1.0


def test_missing_image_raises_error():
    """Verify that attempting to compute an embedding on a non-existent image path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        embedding_service.compute_image_embedding("non_existent_folder/missing_image_12345.png")


def test_db_persistence_and_retrieval(memory_db, sample_image_path: Path):
    """Verify that embedding vectors persist into SQLite JSON columns and deserialize accurately."""
    vec = embedding_service.compute_image_embedding(sample_image_path)

    product = Product(
        sku="TEST-SKU-PERSIST",
        name="Test Persisted Product",
        category="Snacks",
        width_cm=15.0,
        height_cm=22.0,
        depth_cm=8.0,
        image_path=str(sample_image_path),
        embedding=vec,
    )
    memory_db.add(product)
    memory_db.commit()
    memory_db.refresh(product)

    retrieved = memory_db.query(Product).filter(Product.sku == "TEST-SKU-PERSIST").first()
    assert retrieved is not None
    assert retrieved.embedding is not None
    assert len(retrieved.embedding) == 512
    # Verify exact precision preservation
    for original, loaded in zip(vec[:10], retrieved.embedding[:10]):
        assert pytest.approx(original, abs=1e-5) == loaded
