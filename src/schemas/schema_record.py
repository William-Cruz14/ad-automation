from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Action(str, Enum):
    CREATE = "CREATE"
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"

class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Record(BaseModel):
    """
    Classe que representa um registro de auditoria para saber oque o usuário
    criou
    """

    id : UUID = Field(default_factory=uuid4)
    action : Action
    target_username : str
    target_dn : str
    performed_by : str
    source_ip : str | None = None
    error_message : str
    created_at : datetime = Field(default_factory=datetime.now)

