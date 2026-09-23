import pytest
from unittest.mock import AsyncMock, MagicMock
from models.audit_model import ActionEnum, AuditLog
from services.audit_service import create_audit_log


@pytest.mark.asyncio
async def test_create_audit_log_success():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    await create_audit_log(
        db=mock_db,
        operator="admin.user",
        action=ActionEnum.CREATE,
        target="novo.usuario",
        success=True,
        error_message=None
    )

    mock_db.add.assert_called_once()
    added_obj = mock_db.add.call_args[0][0]
    assert isinstance(added_obj, AuditLog)
    assert added_obj.operator == "admin.user"
    assert added_obj.action == ActionEnum.CREATE
    assert added_obj.target == "novo.usuario"
    assert added_obj.success is True
    assert added_obj.error_message is None
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_audit_log_failure_and_rollback():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
    mock_db.rollback = AsyncMock()

    with pytest.raises(Exception) as exc_info:
        await create_audit_log(
            db=mock_db,
            operator="admin.user",
            action=ActionEnum.ENABLE,
            target="alvo.usuario",
            success=False,
            error_message="Erro interno"
        )

    assert "Database error" in str(exc_info.value)
    mock_db.rollback.assert_awaited_once()
