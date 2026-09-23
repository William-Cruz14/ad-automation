import pytest
from unittest.mock import MagicMock, patch
from ldap3.core.exceptions import LDAPInvalidCredentialsResult, LDAPSocketOpenError, LDAPException
from schemas.schema_user import UserCreate, UserResponse, ActivateUserResponse
from core.exceptions import (
    InvalidCredentialsError,
    ConnectionServerError,
    ServerInternalError,
    UserAlreadyExistsError
)
from services import ldap_service


# ==========================================
# Testes: validate_ldap_credentials
# ==========================================

@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_validate_ldap_credentials_success(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_conn.bound = True
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    res = ldap_service.validate_ldap_credentials("admin", "pass123")
    assert res is True


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_validate_ldap_credentials_invalid(mock_server, mock_conn_cls):
    mock_conn_cls.return_value.__enter__.side_effect = LDAPInvalidCredentialsResult(
        result=49, description="invalidCredentials", message="Invalid Credentials", dn=""
    )

    with pytest.raises(InvalidCredentialsError):
        ldap_service.validate_ldap_credentials("admin", "wrongpass")


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_validate_ldap_credentials_socket_error(mock_server, mock_conn_cls):
    mock_conn_cls.return_value.__enter__.side_effect = LDAPSocketOpenError("Host unreachable")

    with pytest.raises(ConnectionServerError):
        ldap_service.validate_ldap_credentials("admin", "pass123")


# ==========================================
# Testes: search_user
# ==========================================

@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_search_user_found(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_attributes_as_dict = {
        "givenName": ["Carlos"],
        "sn": ["Silva"],
        "sAMAccountName": ["carlos.silva"],
        "mail": ["carlos@empresa.com"],
        "department": ["TI"],
        "userAccountControl": [512]
    }
    mock_conn.entries = [mock_entry]
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    result = ldap_service.search_user("carlos.silva")
    assert isinstance(result, UserResponse)
    assert result.username == "carlos.silva"
    assert result.first_name == "Carlos"
    assert result.last_name == "Silva"
    assert result.account_control == 512


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_search_user_not_found(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_conn.entries = []
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    result = ldap_service.search_user("usuario.inexistente")
    assert result is None


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_search_user_empty_username(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    with pytest.raises(ValueError):
        ldap_service.search_user("")


# ==========================================
# Testes: list_users
# ==========================================

@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_list_users_success(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    entry1 = MagicMock()
    entry1.givenName.values = ["Ana"]
    entry1.sn.values = ["Paula"]
    entry1.sAMAccountName.values = ["anapaula"]
    entry1.mail.values = ["ana@empresa.com"]
    entry1.department.values = ["Financeiro"]
    entry1.title.values = ["Analista"]
    entry1.company.values = ["Empresa"]
    entry1.manager.values = ["gerente"]
    entry1.physicalDeliveryOfficeName.values = ["Sede"]
    entry1.employeeID.values = ["2001"]
    entry1.employeeNumber.values = ["EMP2001"]
    entry1.userAccountControl.values = [514]

    mock_conn.entries = [entry1]
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    users = ldap_service.list_users(limit=10)
    assert len(users) == 1
    assert users[0].username == "anapaula"
    assert users[0].first_name == "Ana"


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_list_users_empty(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_conn.entries = []
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    users = ldap_service.list_users()
    assert users == []


# ==========================================
# Testes: add_user
# ==========================================

@patch("services.ldap_service.search_user")
@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_add_user_success(mock_server, mock_conn_cls, mock_search):
    mock_conn = MagicMock()
    mock_conn.add.return_value = True
    mock_conn.result = {'result': 0, 'description': 'success'}
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    expected_user = UserResponse(
        first_name="Novo",
        last_name="Usuario",
        username="novouser",
        department="Tecnologia",
        account_control=514
    )
    mock_search.return_value = expected_user

    user_in = UserCreate(
        first_name="Novo",
        last_name="Usuario",
        username="novouser",
        department="Tecnologia",
        email="novo@empresa.com"
    )
    result = ldap_service.add_user(user_in)
    assert result == expected_user


@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_add_user_failure(mock_server, mock_conn_cls):
    mock_conn = MagicMock()
    mock_conn.add.return_value = False
    mock_conn.result = {'result': 68, 'description': 'entryAlreadyExists'}
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    user_in = UserCreate(
        first_name="Novo",
        last_name="Usuario",
        username="novouser",
        department="Tecnologia",
        email="novo@empresa.com"
    )
    with pytest.raises(ServerInternalError):
        ldap_service.add_user(user_in)


# ==========================================
# Testes: toggle_account
# ==========================================

@patch("services.ldap_service.get_random_password")
@patch("services.ldap_service._get_user_dn")
@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_toggle_account_enable_success(mock_server, mock_conn_cls, mock_get_dn, mock_pwd):
    mock_get_dn.return_value = "CN=Usuario,OU=Users,DC=empresa,DC=local"
    mock_pwd.return_value = "TempPass123!"

    mock_conn = MagicMock()
    mock_conn.result = {'result': 0, 'description': 'success'}
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    res = ldap_service.toggle_account("usuario.teste", enable=True)
    assert isinstance(res, ActivateUserResponse)
    assert res.enabled is True
    assert res.temporary_password == "TempPass123!"


@patch("services.ldap_service._get_user_dn")
@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_toggle_account_disable_success(mock_server, mock_conn_cls, mock_get_dn):
    mock_get_dn.return_value = "CN=Usuario,OU=Users,DC=empresa,DC=local"

    mock_conn = MagicMock()
    mock_conn.result = {'result': 0, 'description': 'success'}
    mock_conn_cls.return_value.__enter__.return_value = mock_conn

    res = ldap_service.toggle_account("usuario.teste", enable=False)
    assert isinstance(res, ActivateUserResponse)
    assert res.enabled is False
    assert res.temporary_password is None


@patch("services.ldap_service._get_user_dn")
@patch("services.ldap_service.Connection")
@patch("services.ldap_service._build_server")
def test_toggle_account_user_not_found(mock_server, mock_conn_cls, mock_get_dn):
    mock_get_dn.return_value = None

    res = ldap_service.toggle_account("inexistente", enable=True)
    assert res is None
