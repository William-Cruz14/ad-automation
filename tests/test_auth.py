import pytest
from httpx import AsyncClient
from decouple import config
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt
from fastapi import HTTPException

from schemas.schema_auth import LoginRequest, TokenResponse
from services import auth_service
from core.exceptions import InvalidCredentialsError, ConnectionServerError

SECRET_KEY = config("SECRET_KEY", default="test_secret_key_jwt_1234567890")
AD_VALID_USER = "test.operator"
AD_VALID_PASSWORD = "ValidPassword123!"


# ==========================================
# Testes Unitários dos Serviços de Auth
# ==========================================

def test_get_token_success():
    login_req = LoginRequest(username=AD_VALID_USER, password=AD_VALID_PASSWORD)
    token_response = auth_service.get_token(login_req)

    assert isinstance(token_response, TokenResponse)
    assert token_response.access_token is not None
    assert token_response.token_type == "bearer"

    payload = jwt.decode(token_response.access_token, SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == AD_VALID_USER
    assert "exp" in payload


def test_verify_token_success():
    payload = {
        "sub": AD_VALID_USER,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    decoded = auth_service.verify_token(token)
    assert decoded["sub"] == AD_VALID_USER


def test_verify_token_expired():
    payload = {
        "sub": AD_VALID_USER,
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        auth_service.verify_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token expirado"


def test_verify_token_invalid():
    with pytest.raises(HTTPException) as exc_info:
        auth_service.verify_token("token_invalido_totalmente_corrompido")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido"


@patch("services.auth_service.validate_ldap_credentials")
def test_authenticate_success(mock_validate):
    mock_validate.return_value = True
    login_req = LoginRequest(username=AD_VALID_USER, password=AD_VALID_PASSWORD)
    result = auth_service.authenticate(login_req)

    mock_validate.assert_called_once_with(AD_VALID_USER, AD_VALID_PASSWORD)
    assert isinstance(result, TokenResponse)
    assert result.access_token is not None


@patch("services.auth_service.validate_ldap_credentials")
def test_authenticate_invalid_credentials_returns_false(mock_validate):
    mock_validate.return_value = False
    login_req = LoginRequest(username=AD_VALID_USER, password="WrongPassword")

    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate(login_req)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Credenciais inválidas."


def test_authenticate_empty_fields():
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate(LoginRequest(username="", password=""))
    assert exc_info.value.status_code == 400


# ==========================================
# Testes de Integração/Rotas de Auth (/auth)
# ==========================================

@pytest.mark.asyncio
@patch("api.auth.authenticate")
async def test_endpoint_login_success(mock_auth, client: AsyncClient):
    mock_auth.return_value = TokenResponse(access_token="fake_jwt_token_123", token_type="bearer")

    response = await client.post("/auth/login", json={
        "username": AD_VALID_USER,
        "password": AD_VALID_PASSWORD
    })

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake_jwt_token_123"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
@patch("api.auth.authenticate")
async def test_endpoint_login_invalid_credentials(mock_auth, client: AsyncClient):
    mock_auth.side_effect = HTTPException(status_code=401, detail="Credenciais inválidas.")

    response = await client.post("/auth/login", json={
        "username": AD_VALID_USER,
        "password": "wrong_password"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas."


@pytest.mark.asyncio
async def test_endpoint_login_empty_body(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "username": "",
        "password": ""
    })
    # Validação do Pydantic / handler de autenticação retorna 400/422
    assert response.status_code in (400, 422)
