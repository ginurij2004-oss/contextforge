import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ==========================================================
# Environment
# ==========================================================

load_dotenv()


# ==========================================================
# Database URL
# ==========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://contextforge:contextforge@localhost:5432/contextforge",
)


# Neon normally provides:
# postgresql://...
#
# ContextForge uses psycopg v3, so convert it for SQLAlchemy.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


# ==========================================================
# Engine
# ==========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ==========================================================
# Session
# ==========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ==========================================================
# Dependency
# ==========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()