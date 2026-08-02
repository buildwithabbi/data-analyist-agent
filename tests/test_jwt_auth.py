"""Unit tests for JWT Authentication & OAuth2 Provider Engine."""

import time
from data_analyst_agent.security.jwt_auth import JWTManager, OAuth2Provider


def test_jwt_issuance_and_verification():
    payload = {"user_id": "usr_123", "username": "abhishek", "role": "admin"}
    token = JWTManager.create_token(payload, expires_in_seconds=3600)

    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    decoded = JWTManager.decode_token(token)
    assert decoded is not None
    assert decoded["user_id"] == "usr_123"
    assert decoded["username"] == "abhishek"
    assert decoded["role"] == "admin"
    assert "exp" in decoded


def test_jwt_expired_token_rejection():
    payload = {"user_id": "usr_123"}
    # Token expired 10 seconds ago
    token = JWTManager.create_token(payload, expires_in_seconds=-10)

    decoded = JWTManager.decode_token(token)
    assert decoded is None


def test_jwt_invalid_signature_rejection():
    payload = {"user_id": "usr_123"}
    token = JWTManager.create_token(payload, secret_key="secret-key-1")

    # Try decoding with wrong secret key
    decoded = JWTManager.decode_token(token, secret_key="wrong-secret-key")
    assert decoded is None


def test_oauth2_provider_auth_url_construction():
    github_url = OAuth2Provider.get_auth_url("github", client_id="gh_client_123", redirect_uri="http://localhost/callback")
    assert "github.com/login/oauth/authorize" in github_url
    assert "gh_client_123" in github_url

    google_url = OAuth2Provider.get_auth_url("google", client_id="goog_client_456", redirect_uri="http://localhost/callback")
    assert "accounts.google.com/o/oauth2/v2/auth" in google_url
    assert "goog_client_456" in google_url
