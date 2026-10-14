from sqlalchemy.ext.asyncio import AsyncSession
from src.models.audit_model import AuditLog, ActionEnum
from src.utils.logging_provider import get_logger

logger = get_logger(__name__)

async def create_audit_log(
        db: AsyncSession,  operator: str,
        action: ActionEnum, target: str, success: bool, error_message: str | None = None):
    """
    Função para criar um log de auditoria no banco de dados.

    :param db: A seção de banco de dados a ser usada.
    :type db: AsyncSession
    :param operator: O usuário que está operando no sistema.
    :type operator: str
    :param action: A ação que foi executada.
    :type action: ActionEnum
    :param target: O usuário ou recurso que foi afetado.
    :type target: str
    :param success: O status se a ação foi bem-sucedida.
    :type success: bool
    :param error_message: O erro que ocorreu ou None se não houver erro.
    :type error_message: str | None
    :return:
    """

    try:
        audit_log = AuditLog(
            operator=operator,
            action=action,
            target=target,
            success=success,
            error_message=error_message
        )

        logger.info(f"Criando log de auditoria")
        db.add(audit_log)

        await db.commit()
        logger.info(f"Log de auditoria criado: {action.value} - {target} - {operator}")

    except Exception as e:
        logger.error(f"Erro ao criar log de auditoria: {e}")
        await db.rollback()
        raise
