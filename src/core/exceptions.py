
class LDAPServiceError(Exception):
    """
    Classe base para todos os erros do nosso domínio.
    Nenhum código levanta essa exceção diretamente, ele serve apenas como "pai".
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(LDAPServiceError):
    pass

class UserNotFoundError(LDAPServiceError):
    pass

class InvalidCredentialsError(LDAPServiceError):
    pass

class ConnectionServerError(LDAPServiceError):
    pass

class InvalidSearchError(LDAPServiceError):
    pass

class PasswordPolicyError(LDAPServiceError):
    pass

class ServerInternalError(LDAPServiceError):
    pass