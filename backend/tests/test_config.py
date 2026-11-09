import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_keeps_local_default_secret():
    settings = Settings(_env_file=None, APP_ENV="development")
    assert settings.secret_key == "change-me-secret-key"


@pytest.mark.parametrize("secret", ["short", "change-me-secret-key", "replace-with-a-unique-random-secret-of-at-least-32-characters"])
def test_production_rejects_weak_or_placeholder_secret(secret):
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, APP_ENV="production", SECRET_KEY=secret)


def test_production_is_blocked_until_managed_database_support_exists():
    secret = "a-unique-production-secret-value-with-more-than-32-bytes"
    with pytest.raises(ValidationError, match="managed database adapter"):
        Settings(_env_file=None, APP_ENV="production", SECRET_KEY=secret)
