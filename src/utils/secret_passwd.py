import secrets
import string

def get_random_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$-"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password



if __name__ == "__main__":
    print(get_random_password())