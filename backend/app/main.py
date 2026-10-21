import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.db.database import init_db
from app.api.routes import health, products, planograms, seed

logger = logging.getLogger("shelfsense")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception handlers
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    orig_msg = str(exc.orig) if hasattr(exc, "orig") and exc.orig else str(exc)
    logger.warning("Database IntegrityError: %s", orig_msg)

    if "UNIQUE constraint failed" in orig_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": f"Conflict: Unique constraint violation. {orig_msg}"},
        )
    if "FOREIGN KEY constraint failed" in orig_msg:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Foreign key constraint failed: referenced entity does not exist or cannot be removed."},
        )
    if "CHECK constraint failed" in orig_msg:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": f"Check constraint failed: physical measurement or value rule violated. {orig_msg}"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"Database integrity error: {orig_msg}"},
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static folder
app.mount(settings.STATIC_URL_PREFIX, StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

# Include routes
app.include_router(health.router)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(planograms.router, prefix=settings.API_V1_PREFIX)
app.include_router(seed.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_PREFIX,
    }
