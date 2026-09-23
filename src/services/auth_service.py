from schemas.schema_auth import TokenResponse, LoginRequest
from fastapi import HTTPException
import jwt
from services.ldap_service import validate_ldap_credentials
from datetime import datetime, timedelta, timezone
from decouple import config


def get_token(user: LoginRequest) -> TokenResponse:
    """
    Função para gerar um token JWT para um usuário autenticado.
    :param user: Um objeto LoginResponse contendo o nome de usuário e a senha.
    :return TokenResponse: Um objeto TokenResponse contendo o token de acesso e o tipo de token.
    """
    try:
        payload = {
            "sub": user.username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        secret_key = config("SECRET_KEY")
        access_token = jwt.encode(payload, secret_key, algorithm="HS256")

        return TokenResponse(access_token=access_token)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar token: {str(e)}")

def verify_token(token: str):
    try:
        secret_key = config("SECRET_KEY")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def authenticate(login: LoginRequest):
    if not login.username or not login.password:
        raise HTTPException(status_code=400, detail="Nome de usuário e senha são obrigatórios.")

    if not validate_ldap_credentials(login.username, login.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    return get_token(user=login)