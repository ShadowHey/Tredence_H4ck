from sqlalchemy import create_engine, event
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

def enable_sqlite_foreign_keys(db_engine):
    """Enforces SQLite foreign key constraints and cascades."""
    @event.listens_for(db_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

if settings.DATABASE_URL.startswith("sqlite"):
    enable_sqlite_foreign_keys(engine)

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
    if use_engine.dialect.name != "sqlite":
        return
    with use_engine.connect() as conn:
        res = conn.exec_driver_sql("PRAGMA table_info(shelves);")
        cols = [row[1] for row in res.fetchall()]
        if cols and "row_heights" not in cols:
            conn.exec_driver_sql("ALTER TABLE shelves ADD COLUMN row_heights TEXT;")
            conn.commit()

        res_prod = conn.exec_driver_sql("PRAGMA table_info(products);")
        prod_cols = [row[1] for row in res_prod.fetchall()]
        if prod_cols and "embedding" not in prod_cols:
            conn.exec_driver_sql("ALTER TABLE products ADD COLUMN embedding JSON;")
            conn.commit()

        res_jobs = conn.exec_driver_sql("PRAGMA table_info(processing_jobs);")
        job_cols = [row[1] for row in res_jobs.fetchall()]
        if job_cols and "audit_snapshot" not in job_cols:
            conn.exec_driver_sql("ALTER TABLE processing_jobs ADD COLUMN audit_snapshot JSON;")
            conn.commit()

        res_outputs = conn.exec_driver_sql("PRAGMA table_info(processed_outputs);")
        output_cols = [row[1] for row in res_outputs.fetchall()]
        if output_cols and "compliance_audit" not in output_cols:
            conn.exec_driver_sql("ALTER TABLE processed_outputs ADD COLUMN compliance_audit JSON;")
            conn.commit()
