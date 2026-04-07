import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db

TEST_DB_FILE = "./test_database.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test
)

import models
Base.metadata.create_all(bind=engine_test)

from main import app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def pytest_sessionfinish(session, exitstatus):
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)