import pytest
import string
from utils.secret_passwd import get_random_password


def test_get_random_password_default_length():
    password = get_random_password()
    assert isinstance(password, str)
    assert len(password) == 8


def test_get_random_password_custom_length():
    password = get_random_password(length=16)
    assert isinstance(password, str)
    assert len(password) == 16


def test_get_random_password_allowed_characters():
    allowed = set(string.ascii_letters + string.digits + "!@#$-")
    for _ in range(50):
        pwd = get_random_password(length=20)
        assert set(pwd).issubset(allowed)


def test_get_random_password_randomness():
    pwd1 = get_random_password(16)
    pwd2 = get_random_password(16)
    assert pwd1 != pwd2
