import os


# ==========================================================
# IMPORTANT:
# Set test environment BEFORE importing the FastAPI app.
# ==========================================================

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://"
    "contextforge:contextforge"
    "@localhost:5432/contextforge_test"
)

# Keep test vector data separate from development data.
os.environ["QDRANT_COLLECTION"] = (
    "contextforge_documents_test"
)


import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.database import engine


# ==========================================================
# Test Client
# ==========================================================

@pytest.fixture()
def client():

    with TestClient(app) as test_client:

        yield test_client


# ==========================================================
# Clean Test Database
#
# This NEVER points to the normal `contextforge` database
# because DATABASE_URL was overridden above before app import.
# ==========================================================

@pytest.fixture(autouse=True)
def reset_test_database():

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )

    yield

    Base.metadata.drop_all(
        bind=engine
    )
