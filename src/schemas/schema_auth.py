from pydantic import BaseModel

class LoginRequest(BaseModel):
    """
    Schema que representa a requisição para efetuar login.
    """
    username: str
    password: str
    

class TokenResponse(BaseModel):
    """
    Schema que representa a resposta da requisição para efetuar login.
    """
    access_token: str
    token_type: str = "bearer"
