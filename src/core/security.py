from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from services.auth_service import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)