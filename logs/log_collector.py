#!/usr/bin/env python3
"""
ShelfSense AI — Unified Log Collector & Background Job Monitor
==============================================================
Collects, streams, and inspects real-time logs from the Frontend (UI actions),
Backend (FastAPI REST endpoints), and Background Workers (CLIP vector embeddings).

Usage:
  # Stream all incoming logs continuously in real-time
  python logs/log_collector.py --follow

  # Stream ONLY background worker jobs (CLIP embedding computation, backfills, etc.)
  python logs/log_collector.py --jobs --follow

  # Stream ONLY frontend actions (e.g. adding shelves, adding products)
  python logs/log_collector.py --frontend --follow

  # Print a summary of all executed background jobs, latency, and system events
  python logs/log_collector.py --summary

  # Clear the log file to start fresh
  python logs/log_collector.py --clear
"""

import sys
import os
import time
import argparse
import re
from pathlib import Path
from datetime import datetime

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT_DIR / "logs"
LOG_FILE = LOGS_DIR / "logs.txt"

# ANSI Colors for terminal display
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_TIME = "\033[90m"        # Gray
COLOR_BACKEND = "\033[36m"     # Cyan
COLOR_FRONTEND = "\033[34m"    # Blue
COLOR_JOB = "\033[35m"         # Magenta
COLOR_INFO = "\033[32m"        # Green
COLOR_WARN = "\033[33m"        # Yellow
COLOR_ERROR = "\033[31m"       # Red
COLOR_JOB_START = "\033[96m"   # Bright Cyan
COLOR_JOB_DONE = "\033[92m"    # Bright Green
COLOR_JOB_ERR = "\033[91m"     # Bright Red

def format_colored_line(line: str) -> str:
    """Highlight timestamps, log sources, and job status in ANSI colors."""
    if not sys.stdout.isatty():
        return line.rstrip()

    text = line.rstrip()

    # Highlight source tags with optional spaces
    text = re.sub(r"\[BACKEND\s*\]", f"{BOLD}{COLOR_BACKEND}[BACKEND]{RESET}", text)
    text = re.sub(r"\[FRONTEND\s*\]", f"{BOLD}{COLOR_FRONTEND}[FRONTEND]{RESET}", text)
    text = re.sub(r"\[JOB\s*\]", f"{BOLD}{COLOR_JOB}[JOB]{RESET}", text)
    text = re.sub(r"\[SYSTEM\s*\]", f"{DIM}[SYSTEM]{RESET}", text)

    # Highlight levels with optional spaces
    text = re.sub(r"\[INFO\s*\]", f"{COLOR_INFO}[INFO]{RESET}", text)
    text = re.sub(r"\[WARN\s*\]", f"{BOLD}{COLOR_WARN}[WARN]{RESET}", text)
    text = re.sub(r"\[WARNING\s*\]", f"{BOLD}{COLOR_WARN}[WARNING]{RESET}", text)
    text = re.sub(r"\[ERROR\s*\]", f"{BOLD}{COLOR_ERROR}[ERROR]{RESET}", text)

    # Highlight job lifecycle markers
    text = text.replace("[JOB-START:CLIP]", f"{BOLD}{COLOR_JOB_START}[JOB-START:CLIP]{RESET}")
    text = text.replace("[JOB-DONE:CLIP]", f"{BOLD}{COLOR_JOB_DONE}[JOB-DONE:CLIP]{RESET}")
    text = text.replace("[JOB-ERROR:CLIP]", f"{BOLD}{COLOR_JOB_ERR}[JOB-ERROR:CLIP]{RESET}")
    text = text.replace("[ACTION:SHELF_ADD]", f"{BOLD}{COLOR_FRONTEND}[ACTION:SHELF_ADD]{RESET}")
    text = text.replace("[ACTION:PRODUCT_ADD]", f"{BOLD}{COLOR_FRONTEND}[ACTION:PRODUCT_ADD]{RESET}")

    # Dim timestamp at line start
    match = re.match(r"^(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\])", text)
    if match:
        ts = match.group(1)
        text = f"{COLOR_TIME}{ts}{RESET}" + text[len(ts):]

    return text

def append_log(source: str, level: str, tag: str, message: str) -> str:
    """Thread-safe append of a structured log line to logs.txt."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    entry = f"[{now_str}] [{source.upper():<8}] [{level.upper():<5}] [{tag}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
        f.flush()
    return entry

def stream_logs(follow: bool = True, lines_count: int = 25, filter_jobs: bool = False,
                filter_fe: bool = False, filter_be: bool = False, filter_err: bool = False):
    """Stream and filter log entries from logs.txt."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()

    def matches_filter(line: str) -> bool:
        if filter_jobs and "[JOB" not in line:
            return False
        if filter_fe and "[FRONTEND" not in line:
            return False
        if filter_be and "[BACKEND" not in line:
            return False
        if filter_err and "[ERROR" not in line and "[WARN" not in line:
            return False
        return True

    # Read last N matching lines
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    filtered_initial = [l for l in all_lines if matches_filter(l)]
    for line in filtered_initial[-lines_count:]:
        print(format_colored_line(line))

    if not follow:
        return

    print(f"\n{COLOR_TIME}--- Streaming new entries (Press Ctrl+C to exit) ---{RESET}\n", flush=True)

    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                if matches_filter(line):
                    print(format_colored_line(line), flush=True)
            else:
                time.sleep(0.1)

def print_summary():
    """Analyze logs.txt and print summary metrics."""
    if not LOG_FILE.exists():
        print("No log file found at logs/logs.txt.")
        return

    total_lines = 0
    jobs_started = 0
    jobs_finished = 0
    jobs_failed = 0
    job_durations = []
    fe_actions = 0
    be_requests = 0
    errors = 0

    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            total_lines += 1
            if "[JOB-START" in line:
                jobs_started += 1
            elif "[JOB-DONE" in line:
                jobs_finished += 1
                # Try extract duration
                m = re.search(r"Duration:\s*([\d\.]+)ms", line)
                if m:
                    try:
                        job_durations.append(float(m.group(1)))
                    except ValueError:
                        pass
            elif "[JOB-ERROR" in line:
                jobs_failed += 1
            if "[FRONTEND" in line:
                fe_actions += 1
            if "[BACKEND" in line:
                be_requests += 1
            if "[ERROR" in line:
                errors += 1

    avg_duration = (sum(job_durations) / len(job_durations)) if job_durations else 0.0

    print("=" * 65)
    print("📊 ShelfSense AI — Log Stream & Background Job Summary")
    print("=" * 65)
    print(f"Total Log Events Recorded : {total_lines}")
    print(f"Backend API Events        : {be_requests}")
    print(f"Frontend Actions          : {fe_actions}")
    print(f"Errors / Failures         : {errors}")
    print("-" * 65)
    print("⚙ Background Worker Jobs (CLIP Embeddings):")
    print(f"  • Jobs Initiated        : {jobs_started}")
    print(f"  • Jobs Completed        : {jobs_finished}")
    print(f"  • Jobs Failed           : {jobs_failed}")
    if job_durations:
        print(f"  • Average Job Latency   : {avg_duration:.2f} ms (min: {min(job_durations):.1f}ms, max: {max(job_durations):.1f}ms)")
    print("=" * 65)

def clear_logs():
    """Clear logs.txt."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    append_log("SYSTEM", "INFO", "LOGS_INITIALIZED", f"Log stream cleared and initialized at {now_str}")
    print(f"✔ Log stream cleared. Active log file: {LOG_FILE}")

def main():
    parser = argparse.ArgumentParser(description="ShelfSense AI Unified Log Collector & Monitor")
    parser.add_argument("-f", "--follow", action="store_true", default=False,
                        help="Stream incoming logs continuously in real-time (like tail -f)")
    parser.add_argument("-n", "--lines", type=int, default=25,
                        help="Number of initial lines to display (default: 25)")
    parser.add_argument("-j", "--jobs", action="store_true", default=False,
                        help="Filter only background worker jobs (CLIP embeddings, tasks)")
    parser.add_argument("--frontend", action="store_true", default=False,
                        help="Filter only frontend UI actions")
    parser.add_argument("--backend", action="store_true", default=False,
                        help="Filter only backend API events")
    parser.add_argument("--errors", action="store_true", default=False,
                        help="Filter only warnings and errors")
    parser.add_argument("-s", "--summary", action="store_true", default=False,
                        help="Display summary metrics of background jobs and events")
    parser.add_argument("--clear", action="store_true", default=False,
                        help="Clear the current log file")
    parser.add_argument("--test", action="store_true", default=False,
                        help="Emit test events for backend, frontend, and background job")

    args = parser.parse_args()

    if args.clear:
        clear_logs()
        return

    if args.summary:
        print_summary()
        return

    if args.test:
        print("Emitting test events to logs.txt...")
        append_log("FRONTEND", "INFO", "ACTION:SHELF_ADD", "User created test shelf 'Beverage Cooler' (120x180cm, 4 rows)")
        append_log("BACKEND", "INFO", "HTTP:POST", "/api/v1/shelves -> 201 Created (14.2ms)")
        append_log("JOB", "INFO", "JOB-START:CLIP", "Task: clip_embedding | Product: #99 ('Test Cola') | SKU: TEST-099")
        time.sleep(0.04)
        append_log("JOB", "INFO", "JOB-DONE:CLIP", "Task: clip_embedding | Product: #99 | 512-dim vector stored in SQLite | Duration: 40.2ms")
        print("✔ Test events emitted.")
        return

    # Default behavior: if no flags or follow specified
    try:
        stream_logs(
            follow=args.follow,
            lines_count=args.lines,
            filter_jobs=args.jobs,
            filter_fe=args.frontend,
            filter_be=args.backend,
            filter_err=args.errors
        )
    except KeyboardInterrupt:
        print(f"\n{COLOR_TIME}Log monitoring stopped.{RESET}")

if __name__ == "__main__":
    main()
