"""
ShelfSense AI — Frontend Event Ingestion Router
================================================
Receives client-side UI action events (such as adding shelves, manual products,
and visual changes) and directs them into the unified logs.txt file.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, status
from app.core.logging_config import log_frontend

router = APIRouter(prefix="/logs", tags=["Logs"])

class FrontendLogPayload(BaseModel):
    event: str = Field(..., description="Event tag, e.g. ACTION:SHELF_ADD, ACTION:PRODUCT_ADD")
    message: str = Field(..., description="Descriptive human-readable event log message")
    level: str = Field("INFO", description="Event severity: INFO, WARN, ERROR")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured metadata")

@router.post("/event", status_code=status.HTTP_200_OK)
def ingest_frontend_event(payload: FrontendLogPayload):
    """
    Ingest a client-side action event and append it to logs.txt.
    """
    tag = payload.event.strip()
    log_frontend(
        level=payload.level.upper(),
        tag=tag,
        message=payload.message.strip()
    )
    return {"status": "ok", "event": tag}
