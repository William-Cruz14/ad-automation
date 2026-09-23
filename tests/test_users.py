import pytest
from httpx import AsyncClient
from unittest.mock import patch
from schemas.schema_user import UserResponse, ActivateUserResponse
from core.exceptions import UserAlreadyExistsError, UserNotFoundError, ServerInternalError, PasswordPolicyError

MOCK_USER_DICT = {
    "first_name": "Joao",
    "last_name": "Silva",
    "username": "joaosilva",
    "email": "joao.silva@empresa.com",
    "department": "Tecnologia",
    "job_title": "Analista",
    "company": "Empresa",
    "manager": "gerente",
    "office": "Matriz",
    "employee_id": "1001",
    "employee_number": "EMP1001",
    "account_control": 514
}

MOCK_USER_RESPONSE = UserResponse(**MOCK_USER_DICT)


# ==========================================
# Testes de Autenticação nas Rotas de Usuários
# ==========================================

@pytest.mark.asyncio
async def test_listar_usuarios_sem_token(client: AsyncClient):
    response = await client.get("/users/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_listar_usuarios_token_invalido(client: AsyncClient):
    response = await client.get("/users/", headers={"Authorization": "Bearer token_invalido"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_criar_usuario_sem_token(client: AsyncClient):
    response = await client.post("/users/", json=MOCK_USER_DICT)
    assert response.status_code == 401


# ==========================================
# Testes de Listagem de Usuários (GET /users/)
# ==========================================

@pytest.mark.asyncio
@patch("services.ldap_service.list_users")
async def test_listar_usuarios_sucesso(mock_list, client: AsyncClient, auth_headers: dict):
    mock_list.return_value = [MOCK_USER_RESPONSE]

    response = await client.get("/users/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["username"] == "joaosilva"


@pytest.mark.asyncio
@patch("services.ldap_service.list_users")
async def test_listar_usuarios_erro_servidor(mock_list, client: AsyncClient, auth_headers: dict):
    mock_list.side_effect = ServerInternalError("Erro interno no servidor LDAP")

    response = await client.get("/users/", headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Erro interno no servidor LDAP"


# ==========================================
# Testes de Criação de Usuário (POST /users/)
# ==========================================

@pytest.mark.asyncio
@patch("services.ldap_service.add_user")
async def test_criar_usuario_sucesso(mock_add, client: AsyncClient, auth_headers: dict):
    mock_add.return_value = MOCK_USER_RESPONSE

    response = await client.post("/users/", json=MOCK_USER_DICT, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "joaosilva"
    assert data["first_name"] == "Joao"


@pytest.mark.asyncio
@patch("services.ldap_service.add_user")
async def test_criar_usuario_ja_existente(mock_add, client: AsyncClient, auth_headers: dict):
    mock_add.side_effect = UserAlreadyExistsError("Usuário já existe no AD")

    response = await client.post("/users/", json=MOCK_USER_DICT, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Usuário já existe no AD"


@pytest.mark.asyncio
@patch("services.ldap_service.add_user")
async def test_criar_usuario_erro_servidor(mock_add, client: AsyncClient, auth_headers: dict):
    mock_add.side_effect = ServerInternalError("Erro interno no LDAP")

    response = await client.post("/users/", json=MOCK_USER_DICT, headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Erro interno no LDAP"


# ==========================================
# Testes de Criação em Lote (POST /users/bulk/)
# ==========================================

@pytest.mark.asyncio
@patch("services.ldap_service.add_user")
async def test_criar_usuarios_bulk_sucesso(mock_add, client: AsyncClient, auth_headers: dict):
    mock_add.return_value = MOCK_USER_RESPONSE

    users_payload = [MOCK_USER_DICT, {**MOCK_USER_DICT, "username": "mariasouza", "first_name": "Maria"}]
    response = await client.post("/users/bulk/", json=users_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
@patch("services.ldap_service.add_user")
async def test_criar_usuarios_bulk_duplicado(mock_add, client: AsyncClient, auth_headers: dict):
    mock_add.side_effect = UserAlreadyExistsError("Usuário já existe")

    users_payload = [MOCK_USER_DICT]
    response = await client.post("/users/bulk/", json=users_payload, headers=auth_headers)
    assert response.status_code == 400


# ==========================================
# Testes de Busca de Usuário (GET /users/{username})
# ==========================================

@pytest.mark.asyncio
@patch("services.ldap_service.search_user")
async def test_buscar_usuario_existente(mock_search, client: AsyncClient, auth_headers: dict):
    mock_search.return_value = MOCK_USER_RESPONSE

    response = await client.get("/users/joaosilva", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "joaosilva"


@pytest.mark.asyncio
@patch("services.ldap_service.search_user")
async def test_buscar_usuario_inexistente(mock_search, client: AsyncClient, auth_headers: dict):
    mock_search.side_effect = UserNotFoundError("Usuário não encontrado")

    response = await client.get("/users/usuario_inexistente", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"


@pytest.mark.asyncio
@patch("services.ldap_service.search_user")
async def test_buscar_usuario_erro_servidor(mock_search, client: AsyncClient, auth_headers: dict):
    mock_search.side_effect = ServerInternalError("Erro no servidor")

    response = await client.get("/users/joaosilva", headers=auth_headers)
    assert response.status_code == 500


# ==========================================
# Testes de Ativação / Desativação (PATCH)
# ==========================================

@pytest.mark.asyncio
@patch("services.ldap_service.toggle_account")
async def test_ativar_usuario_sucesso(mock_toggle, client: AsyncClient, auth_headers: dict):
    mock_toggle.return_value = ActivateUserResponse(
        enabled=True,
        message="Usuário ativado com sucesso",
        temporary_password="TempPassword123!"
    )

    response = await client.patch("/users/joaosilva/enable/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["temporary_password"] == "TempPassword123!"


@pytest.mark.asyncio
@patch("services.ldap_service.toggle_account")
async def test_ativar_usuario_erro_politica_senha(mock_toggle, client: AsyncClient, auth_headers: dict):
    mock_toggle.side_effect = PasswordPolicyError("Senha não atende aos requisitos de complexidade")

    response = await client.patch("/users/joaosilva/enable/", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Senha não atende aos requisitos de complexidade"


@pytest.mark.asyncio
@patch("services.ldap_service.toggle_account")
async def test_ativar_usuario_nao_encontrado(mock_toggle, client: AsyncClient, auth_headers: dict):
    mock_toggle.side_effect = UserNotFoundError("Usuário não encontrado no AD")

    response = await client.patch("/users/usuario_fantasma/enable/", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("services.ldap_service.toggle_account")
async def test_desativar_usuario_sucesso(mock_toggle, client: AsyncClient, auth_headers: dict):
    mock_toggle.return_value = ActivateUserResponse(
        enabled=False,
        message="Usuário desativado com sucesso"
    )

    response = await client.patch("/users/joaosilva/disable/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["message"] == "Usuário desativado com sucesso"


@pytest.mark.asyncio
@patch("services.ldap_service.toggle_account")
async def test_desativar_usuario_nao_encontrado(mock_toggle, client: AsyncClient, auth_headers: dict):
    mock_toggle.side_effect = UserNotFoundError("Usuário não encontrado no AD")

    response = await client.patch("/users/usuario_fantasma/disable/", headers=auth_headers)
    assert response.status_code == 404
