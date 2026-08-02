"""
OAuth2 / OIDC & JWT Authentication Engine
Implements:
1. HMAC-SHA256 Signed JSON Web Token (JWT) Issuance & Validation.
2. OAuth2 / OpenID Connect (OIDC) Single Sign-On (SSO) helpers for Google & GitHub.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional
from urllib.parse import urlencode


DEFAULT_SECRET_KEY = "agentic-ai-production-jwt-secret-key"


def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64_url_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


class JWTManager:
    """Signed JSON Web Token (JWT) manager implementing RFC-7519 standard."""

    @classmethod
    def create_token(
        cls, payload: Dict[str, Any], secret_key: str = DEFAULT_SECRET_KEY, expires_in_seconds: int = 3600
    ) -> str:
        """Issue a signed JWT access token."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload_copy = dict(payload)
        now = int(time.time())
        payload_copy["iat"] = now
        payload_copy["exp"] = now + expires_in_seconds

        header_b64 = _b64_url_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = _b64_url_encode(json.dumps(payload_copy).encode("utf-8"))

        signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(secret_key.encode("utf-8"), signature_input, hashlib.sha256).digest()
        sig_b64 = _b64_url_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    @classmethod
    def decode_token(cls, token: str, secret_key: str = DEFAULT_SECRET_KEY) -> Optional[Dict[str, Any]]:
        """Validate signature and expiration of a JWT access token."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts

            signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(secret_key.encode("utf-8"), signature_input, hashlib.sha256).digest()
            actual_sig = _b64_url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(_b64_url_decode(payload_b64).decode("utf-8"))
            if payload.get("exp", 0) < time.time():
                return None  # Token expired

            return payload
        except Exception:
            return None


class OAuth2Provider:
    """OAuth2 / OpenID Connect (OIDC) Single Sign-On (SSO) Helper."""

    PROVIDERS = {
        "github": {
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user",
            "scope": "read:user user:email",
        },
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scope": "openid email profile",
        },
    }

    @classmethod
    def get_auth_url(cls, provider: str, client_id: str, redirect_uri: str, state: str = "agentic_state") -> str:
        """Construct OAuth2 authorization redirect URL."""
        prov = cls.PROVIDERS.get(provider.lower())
        if not prov:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": prov["scope"],
            "state": state,
            "response_type": "code",
        }
        return f"{prov['auth_url']}?{urlencode(params)}"
