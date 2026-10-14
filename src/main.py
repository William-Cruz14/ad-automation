from fastapi import FastAPI
from src.api import users, auth

app = FastAPI(title="LDAP User Management API", description="API for managing LDAP users", version="1.0.0")
app.include_router(users.router)
app.include_router(auth.router)
