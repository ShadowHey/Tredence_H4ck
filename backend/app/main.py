import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logging_config import setup_unified_logging, log_backend
from app.db.database import init_db
from app.services.image_processing_service import process_pending_jobs, recover_interrupted_jobs
from app.api.routes import health, products, planograms, seed, logs, image_processing

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize unified logging
    setup_unified_logging()
    # Initialize database tables on startup
    init_db()
    # Resume durable image jobs that were in flight if the server previously stopped.
    recover_interrupted_jobs()
    asyncio.create_task(asyncio.to_thread(process_pending_jobs))
    log_backend("INFO", "STARTUP", "FastAPI server and SQLite database initialized.")
    yield
    log_backend("INFO", "SHUTDOWN", "FastAPI server shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Request Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Omit logging the log event ingestion endpoint itself to prevent loop/noise
    path = request.url.path
    if not path.endswith("/logs/event"):
        log_backend(
            level="INFO",
            tag=f"HTTP:{request.method}",
            message=f"{path} -> {response.status_code} ({duration_ms:.1f}ms)"
        )
    return response

# Mount uploads static folder
app.mount(settings.STATIC_URL_PREFIX, StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

# Include routes
app.include_router(health.router)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(planograms.router, prefix=settings.API_V1_PREFIX)
app.include_router(seed.router, prefix=settings.API_V1_PREFIX)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(image_processing.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_PREFIX,
    }
