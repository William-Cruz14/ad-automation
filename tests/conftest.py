import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from decouple import config
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from core.database import get_db
from core.security import get_current_user

SECRET_KEY = config("SECRET_KEY", default="test_secret_key_jwt_1234567890")
AD_VALID_USER = "test.operator"
AD_VALID_PASSWORD = "ValidPassword123!"


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest_asyncio.fixture
async def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    import jwt
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": AD_VALID_USER,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
