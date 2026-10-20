import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.core.config import settings
from app.main import app

@pytest.fixture(scope="session")
def temp_uploads_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_uploads_")
    old_uploads = settings.UPLOADS_DIR
    settings.UPLOADS_DIR = Path(temp_dir)
    yield Path(temp_dir)
    settings.UPLOADS_DIR = old_uploads
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def db_session(temp_uploads_dir):
    """
    Creates a fresh temporary in-memory/file SQLite database for each test.
    Never mutates developer's local persistent database.
    """
    temp_db_file = temp_uploads_dir / f"test_{tempfile.mktemp().split('/')[-1]}.db"
    test_db_url = f"sqlite:///{temp_db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if temp_db_file.exists():
            temp_db_file.unlink(missing_ok=True)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
