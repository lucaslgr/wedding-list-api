import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.schemas import AdminLoginRequest


def _load_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or secret == "change-me" or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a strong value (at least 32 characters)"
        )
    return secret


JWT_SECRET_KEY = _load_jwt_secret_key()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

security = HTTPBearer()


def authenticate_admin(credentials: AdminLoginRequest) -> bool:
    return credentials.username == ADMIN_USERNAME and credentials.password == ADMIN_PASSWORD


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": subject, "exp": int(expires_at.timestamp())}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(JWT_SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Any | None:
    token = credentials.credentials
    try:
        payload = _decode_token(token)
        username = payload.get("sub")
        if username != ADMIN_USERNAME:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def _decode_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_signature = hmac.new(JWT_SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    provided_signature = _b64url_decode(signature_b64)

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise ValueError("Invalid signature")

    payload_raw = _b64url_decode(payload_b64)
    payload = json.loads(payload_raw.decode())
    exp = payload.get("exp")
    if not isinstance(exp, int) or datetime.now(timezone.utc).timestamp() > exp:
        raise ValueError("Expired token")
    return payload


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")
