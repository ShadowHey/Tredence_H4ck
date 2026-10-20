from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(target_engine=None):
    use_engine = target_engine or engine
    Base.metadata.create_all(bind=use_engine)
    try:
        with use_engine.connect() as conn:
            res = conn.exec_driver_sql("PRAGMA table_info(shelves);")
            cols = [row[1] for row in res.fetchall()]
            if cols and "row_heights" not in cols:
                conn.exec_driver_sql("ALTER TABLE shelves ADD COLUMN row_heights TEXT;")
                conn.commit()
    except Exception:
        pass
