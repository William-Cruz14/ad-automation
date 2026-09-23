from sqlalchemy import String, Boolean, Integer, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class ActionEnum(str, enum.Enum):
    CREATE = "CREATE"
    SEARCH = "SEARCH"
    LIST = "LIST"
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operator: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(Enum(ActionEnum), nullable=False)
    target: Mapped[str] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())