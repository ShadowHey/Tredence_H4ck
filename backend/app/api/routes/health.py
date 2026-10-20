from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test DB connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    uploads_ok = settings.UPLOADS_DIR.exists()

    return {
        "status": "ok" if db_status == "healthy" and uploads_ok else "degraded",
        "database": db_status,
        "uploads_dir": str(settings.UPLOADS_DIR),
        "uploads_accessible": uploads_ok,
    }
