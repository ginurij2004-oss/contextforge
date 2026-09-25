from app.core.config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ==========================================================
# Database Engine
# ==========================================================

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


# ==========================================================
# Session Factory
# ==========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ==========================================================
# FastAPI Database Dependency
# ==========================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()
