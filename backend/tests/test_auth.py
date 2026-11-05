import pytest
from fastapi import HTTPException
from backend.app.auth import is_auth_enforced, verify_token


def test_auth_not_enforced_by_default(monkeypatch):
    monkeypatch.delenv("AUTH_ENFORCE", raising=False)
    assert not is_auth_enforced()
    user = verify_token(None)
    assert user["sub"] == "anonymous"


def test_auth_enforced_requires_header(monkeypatch):
    monkeypatch.setenv("AUTH_ENFORCE", "true")
    assert is_auth_enforced()
    with pytest.raises(HTTPException) as exc_info:
        verify_token(None)
    assert exc_info.value.status_code == 401


def test_auth_enforced_with_test_token(monkeypatch):
    monkeypatch.setenv("AUTH_ENFORCE", "true")
    monkeypatch.setenv("AUTH_SKIP_NETWORK", "true")
    user = verify_token("Bearer test-token-12345")
    assert user["email"] == "test@consensusprobe.local"
