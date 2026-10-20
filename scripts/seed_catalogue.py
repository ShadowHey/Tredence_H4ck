#!/usr/bin/env python3
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import SessionLocal, init_db
from app.api.routes.seed import seed_sample_catalogue

def main():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()
    try:
        print("Seeding sample catalogue...")
        result = seed_sample_catalogue(db)
        print(f"Result: {result}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
