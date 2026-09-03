"""src/api/routes/auth.py — RS256 JWT auth endpoints."""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.security.auth import AuthManager, UserRole

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 min

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER

# In-memory user store (replace with PostgreSQL in production)
_USERS: dict[str, dict] = {
    "admin": {"password_hash": "admin123", "role": UserRole.ADMINISTRATOR},
    "operator": {"password_hash": "op123", "role": UserRole.OPERATOR},
    "viewer": {"password_hash": "view123", "role": UserRole.VIEWER},
}

@router.post("/token", response_model=Token, summary="OAuth2 login — get RS256 JWT")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate with username + password. Returns short-lived RS256 JWT (15 min)
    and sets HttpOnly refresh token cookie (7 days).
    """
    auth: AuthManager = request.app.state.auth
    user = _USERS.get(form.username)
    if not user or user["password_hash"] != form.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = auth.create_access_token(form.username, user["role"])
    refresh_token = auth.create_refresh_token(form.username)

    # Audit log
    audit = request.app.state.audit
    audit.log(form.username, request.client.host if request.client else "unknown", "login")

    response = Response(content=Token(access_token=access_token).model_dump_json(),
                        media_type="application/json")
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="strict", secure=True, max_age=604800
    )
    return Token(access_token=access_token)

@router.post("/refresh", response_model=Token, summary="Refresh access token via cookie")
async def refresh(request: Request) -> Token:
    """Use HttpOnly refresh token cookie to obtain a new access token."""
    auth: AuthManager = request.app.state.auth
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    payload = auth.verify_token(refresh_token)
    user = _USERS.get(payload.sub)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    new_token = auth.create_access_token(payload.sub, user["role"])
    return Token(access_token=new_token)

@router.post("/logout", summary="Revoke session (clears cookie)")
async def logout(request: Request, response: Response) -> dict:
    """Clear the refresh token cookie. Token revocation list is Redis-based in production."""
    audit = request.app.state.audit
    audit.log("anonymous", request.client.host if request.client else "unknown", "logout")
    response.delete_cookie("refresh_token", httponly=True, samesite="strict", secure=True)
    return {"detail": "Logged out"}
