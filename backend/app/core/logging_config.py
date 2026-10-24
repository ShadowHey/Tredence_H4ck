"""
ShelfSense AI — Backend & Unified File Logging Configuration
=============================================================
Manages unified log persistence to root `logs/logs.txt` across
FastAPI HTTP endpoints, background worker jobs, and client events.
"""

import sys
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.config import settings

# Unified logs file at repository root
ROOT_DIR = settings.BASE_DIR.parent
LOGS_DIR = ROOT_DIR / "logs"
LOG_FILE = LOGS_DIR / "logs.txt"

_lock = threading.Lock()

def ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def append_unified_log(source: str, level: str, tag: str, message: str):
    """
    Thread-safe write of a structured log entry into root `logs/logs.txt`.
    Ensures immediate line flush so streaming readers (like log_collector.py)
    receive updates without delay.
    """
    try:
        ensure_logs_dir()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{now_str}] [{source.upper():<8}] [{level.upper():<5}] [{tag}] {message}\n"
        with _lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
    except Exception as e:
        # Avoid crashing application if disk logging encounters an issue
        sys.stderr.write(f"[LoggingError] Failed to write to {LOG_FILE}: {e}\n")

def log_backend(level: str, tag: str, message: str):
    """Log a backend server or API event."""
    append_unified_log("BACKEND", level, tag, message)

def log_frontend(level: str, tag: str, message: str):
    """Log a frontend UI action or client event."""
    append_unified_log("FRONTEND", level, tag, message)

def log_job_start(job_name: str, task_id: str, details: str):
    """Log background worker job initiation."""
    append_unified_log("JOB", "INFO", f"JOB-START:{job_name.upper()}", f"Task: {task_id} | {details}")

def log_job_done(job_name: str, task_id: str, duration_ms: float, details: str):
    """Log background worker job completion with duration."""
    append_unified_log("JOB", "INFO", f"JOB-DONE:{job_name.upper()}", f"Task: {task_id} | {details} | Duration: {duration_ms:.1f}ms")

def log_job_error(job_name: str, task_id: str, error_msg: str):
    """Log background worker job failure."""
    append_unified_log("JOB", "ERROR", f"JOB-ERROR:{job_name.upper()}", f"Task: {task_id} | Error: {error_msg}")

class UnifiedFileLogHandler(logging.Handler):
    """Custom logging handler to redirect standard Python logger output to logs.txt."""
    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            source = "BACKEND"
            level = record.levelname
            tag = record.name.split(".")[-1].upper()
            if tag == "ERROR" and level != "ERROR":
                tag = "SERVER"
            append_unified_log(source, level, tag, msg)
        except Exception:
            self.handleError(record)

def setup_unified_logging():
    """Attach the unified file handler to standard app loggers."""
    ensure_logs_dir()
    handler = UnifiedFileLogHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    # Attach to root and uvicorn loggers
    logging.getLogger("app").addHandler(handler)
    logging.getLogger("uvicorn.error").addHandler(handler)
