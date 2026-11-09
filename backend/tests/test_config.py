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


def test_production_accepts_unique_secret_of_at_least_32_bytes():
    secret = "a-unique-production-secret-value-with-more-than-32-bytes"
    settings = Settings(_env_file=None, APP_ENV="production", SECRET_KEY=secret)
    assert settings.secret_key == secret
