from ldap3 import Server, Connection, ALL, Tls, MODIFY_REPLACE
from ldap3.utils.conv import escape_filter_chars
from ldap3.core.exceptions import LDAPException, LDAPInvalidCredentialsResult, LDAPSocketOpenError
from core.exceptions import *
from schemas.schema_user import UserCreate, UserResponse, ActivateUserResponse
from utils.logging_provider import get_logger
import ssl
from decouple import config
from utils.secret_passwd import get_random_password

AD_SERVER = config('AD_SERVER')
BASE_DN = f"DC={AD_SERVER.split('.')[1]},DC={AD_SERVER.split('.')[-1]}"
OU_DN = config('OU_DN')

logger = get_logger(__name__)



def _build_server() -> Server:
    """
    Cria e configura uma conexão segura com o servidor Active Directory.

    Esta função configura uma instância de servidor com criptografia TLS e 
    configurações específicas de protocolo e validação para comunicação segura. 
    O servidor se conecta a um servidor Active Directory predefinido em uma porta 
    específica usando as configurações de segurança fornecidas.

    Atenção em produção o ideal é usar o ssl.CERT_REQUIRED com o seu respectivo arquivo
    de certificado de uma CA, mas para testes podem usar ssl.CERT_NONE.

    Returns:
        Uma instância de Server configurada e pronta para uso.

    """
    tls = Tls(
        validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2,
        ca_certs_file=config('CA_FILE_PATH')
    )
    return Server(AD_SERVER, port=636, use_ssl=True, get_info=ALL, tls=tls)


def validate_ldap_credentials(username: str, password: str) -> bool:
    """
    Função que valida as credenciais de quem está tentando se conectar ao Active Directory.

    :param username: O username do usuário que quer se conectar.
    :type username: str
    :param password: A senha para o usuário que quer se conectar.
    :type password: str
    :return: Um valor booleano True ou False.
    :rtype: bool
    """
    try:
        with Connection(
            _build_server(),
            user=username,password=password,
            authentication='SIMPLE', auto_bind=True) as conn:

            return conn.bound

    except LDAPInvalidCredentialsResult as error:

        logger.warning(f"Credenciais inválidas para usuário -> {username}: {error}")

        raise InvalidCredentialsError("Usuário ou senha incorretos. Tente novamente.")

    except LDAPSocketOpenError as error:

        logger.error(f"Erro ao conectar ao servidor AD: {error}")

        raise ConnectionServerError(f"Erro ao conectar ao servidor AD")



def add_user(user_data: UserCreate) -> UserResponse | None:
    """
    Função responsável por criar um usuário no Active Directory.

    :param user_data: Uma instância de UserCreate com os dados necessário para criar o usuário.
    :type user_data: UserCreate
    :return: Uma instância de UserResponse como um resumo do usuário criado.
    :rtype: UserResponse
    """
    with Connection(
            _build_server(),
            user=config("LDAP_USER"), password=config("LDAP_PASSWORD"),
            authentication='SIMPLE', auto_bind=True) as conn:

        try:
            logger.info("Tentando criar usuário no AD...")
            full_name = f"{user_data.first_name} {user_data.last_name}"
            dn = f"CN={full_name},{OU_DN}"
            object_class = ['top', 'person', 'organizationalPerson', 'user']
            attributes = {
                'objectClass': object_class,
                'cn': full_name,
                'sn': user_data.last_name,
                'givenName': user_data.first_name,
                'sAMAccountName': user_data.username,
                'userPrincipalName': f"{user_data.username}@{config('DOMINIO')}",
                'mail': user_data.email,
                'userAccountControl': 514,
                **({'department': user_data.department} if user_data.department else {}),
                **({'title': user_data.job_title} if user_data.job_title else {}),
                **({'company': user_data.company} if user_data.company else {}),
                **({'manager': user_data.manager} if user_data.manager else {}),
                **({'physicalDeliveryOfficeName': user_data.office} if user_data.office else {}),
                **({'employeeID': user_data.employee_id} if user_data.employee_id else {}),
                **({'employeeNumber': user_data.employee_number} if user_data.employee_number else {}),
            }

            logger.info(f"Tentando criar o usuário no DN: {dn}")

            success = conn.add(dn=dn, object_class=object_class, attributes=attributes)

            if success and conn.result['result'] == 0:

                logger.info(f"Usuário {full_name} criado com sucesso!")

                return search_user(user=user_data.username)

            else:

                logger.error(f"Falha ao criar usuário: {conn.result}")

                raise LDAPException(f"Falha ao criar usuário: {conn.result['description']}")

        except UserAlreadyExistsError as error:

            logger.info(f"Usuário {user_data.username} já existe no AD. erro: {error}")

            raise error

        except LDAPException as error:

            logger.error(f"Erro ao criar usuário >> {error}")
            logger.error(f"Erro >> {conn.result}")

            raise ServerInternalError("Erro interno do servidor.")

def list_users(limit: int = 50) -> list[UserResponse]:
    """
    Função responsável por listar todos usuários do Active Directory com base no limite de busca.

    :param limit: Um limite de busca para o Active Directory.
    :type: limit: int
    :return: Uma lista de instâncias de UserResponse.
    :rtype: list[UserResponse]
    """
    with Connection(
            _build_server(),
            user=config("LDAP_USER"), password=config("LDAP_PASSWORD"),
            authentication='SIMPLE', auto_bind=True) as conn:
        try:
            conn.search(
                search_base=OU_DN,
                search_filter="(objectClass=user)",
                attributes=[
                    'cn', 'mail', 'sAMAccountName', 'userAccountControl', 'givenName',
                    'sn', 'department', 'title', 'company', 'manager',
                    'physicalDeliveryOfficeName', 'employeeID', 'employeeNumber'
                ],
                size_limit=limit
            )

            if not conn.entries:
                logger.info("Ao listar nenhum usuário foi encontrado.")
                return []


            logger.info(f"{len(conn.entries)} usuários encontrados.")
            return [
                UserResponse(
                    first_name=entry.givenName.values[0],
                    last_name=entry.sn.values[0],
                    username=entry.sAMAccountName.values[0],
                    email=entry.mail.values[0] if entry.mail.values else None,
                    department=entry.department.values[0] if entry.department.values else None,
                    job_title=entry.title.values[0] if entry.title.values else None,
                    company=entry.company.values[0] if entry.company.values else None,
                    manager=entry.manager.values[0] if entry.manager.values else None,
                    office=entry.physicalDeliveryOfficeName.values[0] if entry.physicalDeliveryOfficeName.values else None,
                    employee_id=entry.employeeID.values[0] if entry.employeeID.values else None,
                    employee_number=entry.employeeNumber.values[0] if entry.employeeNumber.values else None,
                    account_control=entry.userAccountControl.values[0]
                ) for entry in conn.entries
            ]
        except LDAPException as error:

            logger.error(f"Erro ao listar usuários: {error}")

            raise ServerInternalError("Erro interno do servidor.")

        except LDAPSocketOpenError as error:

            logger.error(f"Erro ao conectar ao servidor AD: {error}")

            raise ConnectionServerError(f"Erro ao conectar ao servidor AD")

def search_user(user: str) -> UserResponse | None:
    """
    Função responsável por buscar usuário no Active Directory com base no login.

    :param user: O username de quem deseja buscar.
    :type user: str
    :return: Uma instância de UserResponse com os dados do usuário encontrado ou None.
    :rtype: UserResponse | None
    """

    with Connection(
            _build_server(),
            user=config("LDAP_USER"), password=config("LDAP_PASSWORD"),
            authentication='SIMPLE', auto_bind=True) as conn:
        try:

            if not user:
                raise ValueError("Informe o username para busca.")

            safe_filter = escape_filter_chars(user)

            conn.search(
                search_base = OU_DN,
                search_filter = f"(sAMAccountName={safe_filter})",

                attributes = [
                    'cn', 'mail', 'sAMAccountName', 'userAccountControl', 'department', 'givenName', 'sn' ]
            )

            if conn.entries:
                result = conn.entries[0].entry_attributes_as_dict
                return UserResponse(
                    first_name=result.get('givenName', [None])[0],
                    last_name=result.get('sn', [None])[0],
                    username=result['sAMAccountName'][0],
                    email=result['mail'][0] if result['mail'] else None,
                    department=result['department'][0] if result['department'] else None,
                    account_control=result['userAccountControl'][0]
                )

            return None

        except LDAPSocketOpenError as error:
            logger.error(f"Erro ao conectar ao servidor AD: {error}")

            raise ConnectionServerError(f"Erro ao conectar ao servidor AD")

        except LDAPException as error:
            logger.error(f"Erro ao buscar usuário: {error}")

            raise ServerInternalError("Erro interno do servidor.")


def _get_user_dn(login: str) -> str | None:
    """
    Função responsável por buscar o dn ao qual o usuário pertence no Active Directory.

    :param login: O username do usuário que quer buscar o dn.
    :type login: str
    :return: Retorna uma string com o dn buscado ou None.
    :rtype: str | None
    """
    with Connection(
            _build_server(),
            user=config("LDAP_USER"), password=config("LDAP_PASSWORD"),
            authentication='SIMPLE', auto_bind=True) as conn:
        safe_login = escape_filter_chars(login)
        conn.search(
            search_base=OU_DN,
            search_filter=f"(sAMAccountName={safe_login})",
            attributes=['distinguishedName']
        )

        if conn.entries:
            return conn.entries[0].entry_dn

        return None


def toggle_account(user: str, enable: bool) -> ActivateUserResponse | None :
    """
    Função responsável por ativar ou desativar uma conta no Active Directory.

    :param user: O username do usuário que quer ativar ou desativar a conta.
    :type user: str
    :param enable: Um valor booleano que indica se a conta deve ser ativada ou desativada.
    :type enable: bool
    :return: Uma instância de ActivateUserResponse com campos informativos ou None.
    :rtype: ActivateUserResponse | None
    """
    with Connection(
            _build_server(),
            user=config("LDAP_USER"), password=config("LDAP_PASSWORD"),
            authentication='SIMPLE', auto_bind=True) as conn:

        try:
            logger.info(f"Tentando {'ativar' if enable else 'desativar'} conta do usuário {user}.")

            dn = _get_user_dn(user)
            if not dn:
                logger.warning(f"Usuário {user} não encontrado.")
                return None

            if dn and enable:
                password = get_random_password()
                encoded_password = '"{}"'.format(password).encode('utf-16-le')

                conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [encoded_password])]})

                if conn.result['result'] != 0:
                    logger.error(f"Erro ao definir senha: {conn.result}")
                    raise Exception(conn.result['description'])

                conn.modify(dn, {'pwdLastSet': [(MODIFY_REPLACE, [0])]})

                if conn.result['result'] != 0:
                    logger.error(f"Erro ao definir senha: {conn.result}")
                    raise Exception(conn.result['description'])

                uac = 512
                conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [uac])]})

                if conn.result['result'] != 0:
                    logger.error(f"Erro ao ativar o usuário: {conn.result}")
                    raise Exception(conn.result['description'])

                logger.info(f"Usuário {user} ativado com sucesso.")

                return ActivateUserResponse(
                    enabled=enable,
                    message="Usuário ativado com sucesso",
                    temporary_password=password
                )
            else:
                uac = 514
                conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [uac])]})

                if conn.result['result'] != 0:
                    logger.error(f"Erro ao tentar desativar usuário: {conn.result}")
                    raise Exception(conn.result['description'])

                return ActivateUserResponse(
                    enabled=enable,
                    message="Usuário desativado com sucesso"
                )

        except LDAPException as error:
            logger.error(f"Erro ao alterar conta {user}: {error}")
            raise ServerInternalError("Erro interno do servidor.")
        except LDAPSocketOpenError as error:
            logger.error(f"Erro ao conectar ao servidor AD: {error}")
            raise ConnectionServerError(f"Erro ao conectar ao servidor AD")
