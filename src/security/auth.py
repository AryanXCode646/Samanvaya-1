"""
src/security/auth.py
RS256 JWT authentication, RBAC enforcement, and Redis-backed rate limiter.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import jwt  # PyJWT
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

try:
    import redis as redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

# ---------------------------------------------------------------------------
# HTTP Security Headers  (inject via middleware on every response)
# ---------------------------------------------------------------------------
SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    ),
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


# ---------------------------------------------------------------------------
# RBAC Roles
# ---------------------------------------------------------------------------
class UserRole(str, Enum):
    VIEWER        = "viewer"         # Read-only inspection, view results
    OPERATOR      = "operator"       # Run pipelines, view GPU telemetry
    ADMINISTRATOR = "administrator"  # Manage users, export, configure cluster


# ---------------------------------------------------------------------------
# Token models
# ---------------------------------------------------------------------------
class TokenPayload(BaseModel):
    sub:  str             # User ID (subject)
    role: UserRole
    exp:  int             # Expiry (Unix timestamp)
    iat:  int             # Issued at
    jti:  str             # JWT ID (for revocation)


@dataclass
class SecurityConfig:
    algorithm: str                  = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int   = 7
    # Keys are populated by generate_key_pair()
    private_key_pem: bytes          = field(default=b"", repr=False)
    public_key_pem: bytes           = field(default=b"", repr=False)


# ---------------------------------------------------------------------------
# AuthManager
# ---------------------------------------------------------------------------
class AuthManager:
    """
    RS256 asymmetric JWT manager with PKCE-compatible OAuth2 flow.

    RS256 rationale:
        Private key signs tokens (never leaves the server).
        Public key verifies — can be distributed to microservices safely.
        Algorithm-confusion attacks (HS256 downgrade) are impossible because
        we reject any token whose header alg != RS256.
    """

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        self.config = config or SecurityConfig()
        if not self.config.private_key_pem:
            self.generate_key_pair()

    def generate_key_pair(self) -> None:
        """Generate a fresh RSA-2048 key pair."""
        if not _JWT_AVAILABLE:
            raise RuntimeError("cryptography + PyJWT packages required for AuthManager")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.config.private_key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        self.config.public_key_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def create_access_token(self, user_id: str, role: UserRole) -> str:
        """Create a short-lived (15 min) RS256 JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub":  user_id,
            "role": role.value,
            "iat":  int(now.timestamp()),
            "exp":  int((now + timedelta(minutes=self.config.access_token_expire_minutes)).timestamp()),
            "jti":  str(uuid.uuid4()),
            "typ":  "access",
        }
        return jwt.encode(payload, self.config.private_key_pem, algorithm="RS256")

    def create_refresh_token(self, user_id: str) -> str:
        """Create a long-lived (7 day) refresh token stored in HttpOnly cookie."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub":  user_id,
            "iat":  int(now.timestamp()),
            "exp":  int((now + timedelta(days=self.config.refresh_token_expire_days)).timestamp()),
            "jti":  str(uuid.uuid4()),
            "typ":  "refresh",
        }
        return jwt.encode(payload, self.config.private_key_pem, algorithm="RS256")

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode a JWT. Raises HTTPException on any failure.
        Rejects: expired tokens, wrong algorithm, missing fields,
        tampered signatures.
        """
        try:
            data = jwt.decode(
                token,
                self.config.public_key_pem,
                algorithms=["RS256"],   # Whitelist ONLY RS256 — no HS256 downgrade
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}")

        role_val = data.get("role", UserRole.VIEWER.value)
        try:
            role = UserRole(role_val)
        except ValueError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid role in token")

        return TokenPayload(
            sub=data["sub"],
            role=role,
            exp=data["exp"],
            iat=data["iat"],
            jti=data["jti"],
        )

    # -----------------------------------------------------------------------
    # FastAPI dependency factories
    # -----------------------------------------------------------------------

    _bearer = HTTPBearer(auto_error=True)

    def require_role(self, *roles: UserRole):
        """
        FastAPI dependency. Usage:
            @router.post("/submit", dependencies=[Depends(auth.require_role(UserRole.OPERATOR))])
        """
        auth_manager = self

        async def _check(
            creds: HTTPAuthorizationCredentials = Depends(auth_manager._bearer),
        ) -> TokenPayload:
            payload = auth_manager.verify_token(creds.credentials)
            if payload.role not in roles:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    f"Role '{payload.role}' insufficient. Required: {[r.value for r in roles]}",
                )
            return payload

        return _check


# ---------------------------------------------------------------------------
# Rate Limiter — sliding window via Redis ZADD/ZREMRANGEBYSCORE
# ---------------------------------------------------------------------------
class RateLimiter:
    """
    Sliding-window rate limiter.

    Primary: Redis ZADD/ZRANGEBYSCORE (accurate, distributed).
    Fallback: In-memory dict (single-instance only, for local dev).

    Usage:
        limiter = RateLimiter(redis_client, max_requests=10, window_seconds=60)
        if not limiter.is_allowed(f"auth:{client_ip}"):
            raise HTTPException(429, "Rate limit exceeded")
    """

    def __init__(
        self,
        redis_client=None,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self._redis = redis_client
        self._max = max_requests
        self._window = window_seconds
        self._fallback: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """
        Returns True if the request is within rate limit.
        Uses Redis sorted sets for O(log N) sliding window.
        """
        now = time.time()
        window_start = now - self._window

        if self._redis and _REDIS_AVAILABLE:
            return self._redis_check(key, now, window_start)
        return self._memory_check(key, now, window_start)

    # ---- Redis path ----
    def _redis_check(self, key: str, now: float, window_start: float) -> bool:
        try:
            pipe = self._redis.pipeline()
            rkey = f"ratelimit:{key}"
            pipe.zremrangebyscore(rkey, 0, window_start)
            pipe.zcard(rkey)
            pipe.zadd(rkey, {str(uuid.uuid4()): now})
            pipe.expire(rkey, self._window + 1)
            results = pipe.execute()
            count_before_add = results[1]
            return count_before_add < self._max
        except Exception:
            # Redis failure → fail open with memory fallback
            return self._memory_check(key, now, window_start)

    # ---- In-memory fallback ----
    def _memory_check(self, key: str, now: float, window_start: float) -> bool:
        timestamps = [t for t in self._fallback.get(key, []) if t > window_start]
        if len(timestamps) >= self._max:
            self._fallback[key] = timestamps
            return False
        timestamps.append(now)
        self._fallback[key] = timestamps
        return True
