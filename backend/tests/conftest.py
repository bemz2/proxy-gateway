from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.services.proxy import connection_manager
from app.tasks.email_tasks import send_activation_email_task


SQLALCHEMY_DATABASE_URL = settings.test_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def _ensure_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database
    if not database_name:
        raise RuntimeError("TEST_DATABASE_URL must include a database name")

    maintenance_url = url.set(database="postgres")
    maintenance_engine = create_engine(
        maintenance_url,
        future=True,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        with maintenance_engine.connect() as connection:
            database_exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            ).scalar()
            if not database_exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        maintenance_engine.dispose()


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    _ensure_database_exists(SQLALCHEMY_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    connection_manager.active_connections.clear()
    connection_manager.ws_tokens.clear()
    connection_manager.statuses.clear()
    yield


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(send_activation_email_task, "delay", lambda *args, **kwargs: None)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
