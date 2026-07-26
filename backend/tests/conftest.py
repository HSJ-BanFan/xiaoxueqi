import os
import sys
from pathlib import Path
from typing import Callable, Dict

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-agent-suite"
os.environ["DEBUG"] = "false"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["AGENT_ENABLED"] = "true"
os.environ["AGENT_REQUIRE_CONFIRM_WRITE"] = "true"
os.environ["LLM_BASE_URL"] = "http://127.0.0.1:9/v1"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "test-model"
os.environ["LLM_TIMEOUT_SECONDS"] = "0.1"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db import models as _models  # noqa: F401
from app.db.base_class import Base
from app.db.models import User
from main import app


TEST_PASSWORD = "StrongTestPassword123!"


@pytest.fixture(scope="session")
def test_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def testing_session_local(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def reset_database(test_engine):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(testing_session_local) -> Session:
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(testing_session_local) -> TestClient:
    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db: Session) -> Callable[..., User]:
    def create_user(
        *,
        email: str,
        name: str,
        password: str = TEST_PASSWORD,
        target_glucose_min: float | None = None,
        target_glucose_max: float | None = None,
    ) -> User:
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False,
            target_glucose_min=target_glucose_min,
            target_glucose_max=target_glucose_max,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return create_user


@pytest.fixture
def user_a(user_factory) -> User:
    return user_factory(email="user-a@example.com", name="用户A")


@pytest.fixture
def user_b(user_factory) -> User:
    return user_factory(email="user-b@example.com", name="用户B")


@pytest.fixture
def auth_header_a(user_a: User) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_a.id)}"}


@pytest.fixture
def auth_header_b(user_b: User) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_b.id)}"}
