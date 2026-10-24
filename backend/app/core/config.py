from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShelfSense AI Planogram Designer"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/shelfsense.db"
    
    # Uploads directory
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    STATIC_URL_PREFIX: str = "/uploads"
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    # File limits
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/svg+xml"
    ]

    IMAGE_PROCESSING_MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024
    IMAGE_PROCESSING_TIMEOUT_SECONDS: int = 300
    IMAGE_PARSING_DIR: Path = BASE_DIR.parent / "image-parsing"

    # Optional server-side Roboflow price-tag inference. Never expose this to the UI.
    ROBOFLOW_API_KEY: Optional[str] = None
    ROBOFLOW_PRICE_TAG_MODEL_ID: str = "price-tag-detection-kjttf/16"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure uploads directory exists
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
