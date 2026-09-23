from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """
    Schema que representa um usuário do Active Directory.
    """
    first_name: str = Field(min_length=4, max_length=10)
    last_name: str = Field(min_length=4, max_length=10)
    username: str = Field(min_length=4, max_length=10)
    email: EmailStr | None = None
    department: str = Field(min_length=4, max_length=10)
    job_title: str | None = Field(default=None, min_length=4, max_length=10)
    company: str | None = Field(default=None, min_length=4, max_length=10)
    manager: str | None = Field(default=None, min_length=4, max_length=10)
    office: str | None = Field(default=None, min_length=4, max_length=10)
    employee_id: str | None = Field(default=None, min_length=4, max_length=10)
    employee_number: str | None = Field(default=None, min_length=4, max_length=10)
    account_control: int = 514


class UserResponse(BaseModel):
    """
    Schema que representa um usuário do Active Directory após ser criado.
    """
    first_name: str
    last_name: str
    username: str
    email: EmailStr | None = None
    department: str | None = None
    job_title: str | None = None
    company: str | None = None
    manager: str | None = None
    office: str | None = None
    employee_id: str | None = None
    employee_number: str | None = None
    account_control: int | None = None


class ActivateUserResponse(BaseModel):
    """
    Schema que representa uma estrutura de resposta da requisição para ativar ou desativar o usuário.
    """
    enabled: bool
    temporary_password: str | None = None
    message: str


