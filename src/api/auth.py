from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from schemas.schema_auth import LoginRequest
from services.auth_service import authenticate

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
async def login(user: LoginRequest):
    return await run_in_threadpool(authenticate,user)
