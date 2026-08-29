import pytest

from roberta.telegram_identity import (
    is_authorized_user,
    owner_id_from_env,
    telegram_thread_id,
)


def test_owner_id_from_explicit_value():
    assert owner_id_from_env("12345") == 12345


@pytest.mark.parametrize("value", ["", "abc", "0", "-7"])
def test_owner_id_rejects_invalid_values(value):
    with pytest.raises(RuntimeError):
        owner_id_from_env(value)


def test_owner_authorization_is_exact():
    assert is_authorized_user(12345, owner_id=12345) is True
    assert is_authorized_user(54321, owner_id=12345) is False
    assert is_authorized_user(None, owner_id=12345) is False


def test_thread_id_is_stable():
    assert telegram_thread_id(user_id=12345, chat_id=12345) == "telegram:12345:12345"
