from fastapi import APIRouter, Depends, BackgroundTasks
from http import HTTPStatus
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from src.core.exceptions import *
from src.core.database import get_db
from src.utils.logging_provider import get_logger
from src.services import ldap_service, audit_service
from src.services.audit_service import create_audit_log, ActionEnum
from src.core.security import get_current_user
from src.schemas.schema_user import UserCreate, UserResponse, ActivateUserResponse

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=list[UserResponse])
async def list_all(
        background_tasks: BackgroundTasks,
        db:AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para listar todos os usuários do Active Directory.

    :param db: A sessão do banco de dados.
    :type db: AsyncSession
    :param background_tasks: A tarefa de background.
    :type background_tasks: BackgroundTasks
    :param current_user: O usuário que está executando a ação.
    :type current_user: dict
    :returns: Uma lista de usuários do Active Directory
    """
    success = False
    error_message = None

    try:
        users = await run_in_threadpool(ldap_service.list_users)

        if isinstance(users[0], UserResponse):
            success = True
            return users

    except UserNotFoundError as error:
        error_message = error.message
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=error_message)
    except ServerInternalError as error:
        error_message = error.message
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)
    finally:
        background_tasks.add_task(
            audit_service.create_audit_log,
            db=db,
            operator=current_user["sub"],
            action=ActionEnum.LIST,
            target="all",
            success=success,
            error_message=error_message
        )


@router.post("/", response_model=UserResponse)
async def create_user(
        background_tasks: BackgroundTasks,
        user: UserCreate, db:AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para criar um novo usuário no Active Directory.

    :param background_tasks: O objeto BackgroundTasks para adicionar tarefas em segundo plano.
    :type background_tasks: BackgroundTasks
    :param user: Os dados do usuário a ser criado.
    :type user: UserCreate
    :param db: A sessão do banco de dados.
    :type db: AsyncSession
    :param current_user: O usuário que está executando a ação.
    :type current_user: dict
    :return: As informações do usuário criado
    :rtype: UserResponse
    """
    success = False
    error_message = ""

    try:
        user = await run_in_threadpool(ldap_service.add_user, user)

        if isinstance(user, UserResponse):
            success = True
            return user

    except UserAlreadyExistsError as error:
        error_message = str(error)
        logger.error(f"Erro ao criar usuário: {error_message}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error_message)
    except ServerInternalError as error:
        error_message = str(error)
        logger.error(f"Erro ao criar usuário: {error_message}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)
    finally:
        background_tasks.add_task(
            create_audit_log,
            db=db,
            operator=current_user["sub"],
            action=ActionEnum.CREATE,
            target=user.username,
            success=success,
            error_message=error_message
        )

@router.get("/{username}", response_model=UserResponse)
async def get_user(
        username: str, background_tasks: BackgroundTasks,
        db:AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Função para buscar um usuário pelo username.

    :param username: Login do usuário.
    :param background_tasks: A background task.
    :param db: Database session.
    :param current_user: O usuário que está executando a operação.
    :return: O usuário encontrado.
    :rtype: UserResponse
    """
    success = False
    error_message = ""

    try:
        search = await run_in_threadpool(ldap_service.search_user, user=username)

        if isinstance(search, UserResponse):
            success = True
            return search

    except UserNotFoundError as error:
        error_message = str(error)
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=error_message)
    except ServerInternalError as error:
        error_message = str(error)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)
    finally:
        background_tasks.add_task(
            create_audit_log,
            db=db,
            operator=current_user["sub"],
            action=ActionEnum.SEARCH,
            target=username,
            success=success,
            error_message=error_message
        )

@router.post("/bulk/", response_model=list[UserResponse])
async def create_users(
        background_tasks: BackgroundTasks,
        users: list[UserCreate],
        db:AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para criar novos usuários em lote no Active Directory.

    :param background_tasks: A background task.
    :type background_tasks: BackgroundTasks
    :param users: Uma lista de dados dos usuários a serem criados.
    :type users: list[UserCreate]
    :param db: A sessão do banco de dados.
    :type db: AsyncSession
    :param current_user: O usuário que está executando a ação.
    :type current_user: dict
    :return: Uma lista com as informações dos usuários criados
    :rtype: list[UserResponse]
    """
    success = False
    error_message = ""
    results = []

    for user in users:

        try:
            created_user = await run_in_threadpool(ldap_service.add_user, user)

            if isinstance(created_user, UserResponse):
                success = True
                results.append(created_user)

        except UserAlreadyExistsError as error:
            error_message = str(error)
            logger.error(f"Erro ao criar o usuário {user.username}: {error_message}")
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error_message)

        except ServerInternalError as error:
            error_message = str(error)
            logger.error(f"Erro ao criar o usuário {user.username}: {error_message}")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)

        finally:
            background_tasks.add_task(
                create_audit_log,
                db=db,
                operator=current_user["sub"],
                action=ActionEnum.CREATE,
                target=user.username,
                success=success,
                error_message=error_message
            )
    return results



@router.patch("/{username}/enable/", response_model=ActivateUserResponse)
async def active_user(
        username: str,
        background_tasks: BackgroundTasks,
        db:AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para habilitar um usuário no Active Directory.

    :param username: O username do usuário a ser habilitado.
    :type username: str
    :param background_tasks: O objeto BackgroundTasks para adicionar tarefas em segundo plano.
    :type background_tasks: BackgroundTasks
    :param db: A sessão do banco de dados.
    :type db: AsyncSession
    :param current_user: O usuário que está executando a ação.
    :type current_user: dict
    :return: Uma mensagem de sucesso ou erro
    """
    success = False
    error_message = ""

    try:
        active = await run_in_threadpool(ldap_service.toggle_account, user=username, enable=True)

        if isinstance(active, ActivateUserResponse):
            success = True
            return active


    except PasswordPolicyError as error:
        error_message = str(error)
        logger.error(f"Erro ao ativar o usuário {username}: {error_message}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error_message)

    except UserNotFoundError as error:
        error_message = str(error)
        logger.error(f"Erro ao ativar o usuário {username}: {error_message}")
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=error_message)

    except ServerInternalError as error:
        error_message = str(error)
        logger.error(f"Erro ao ativar o usuário {username}: {error_message}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)

    finally:
        background_tasks.add_task(
            create_audit_log,
            db=db,
            operator=current_user["sub"],
            action=ActionEnum.ENABLE,
            target=username,
            success=success
        )


@router.patch("/{username}/disable/", response_model=ActivateUserResponse)
async def disable_user(
        username: str,
        background_tasks: BackgroundTasks,
        db:AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para desabilitar um usuário no Active Directory

    :param username: O username do usuário a ser desabilitado.
    :type username: str
    :param background_tasks: O objeto BackgroundTasks para adicionar tarefas em segundo plano.
    :type background_tasks: BackgroundTasks
    :param db: A sessão do banco de dados.
    :type db: AsyncSession
    :param current_user: O usuário que está executando a ação.
    :type current_user: dict
    :return: Uma mensagem de sucesso ou erro
    """

    success = False
    error_message = None

    try:
        disabled = await run_in_threadpool(ldap_service.toggle_account, user=username, enable=False)

        if isinstance(disabled, ActivateUserResponse):
            success = True
            return disabled


    except UserNotFoundError as error:

        error_message = str(error)
        logger.error(f"Erro ao desabilitar o usuário {username}: {error_message}")
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=error_message)


    except ServerInternalError as error:

        error_message = str(error)
        logger.error(f"Erro ao desabilitar o usuário {username}: {error_message}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_message)


    finally:

        background_tasks.add_task(
            create_audit_log,
            db=db,
            operator=current_user["sub"],
            action=ActionEnum.DISABLE,
            target=username,
            success=success
        )
