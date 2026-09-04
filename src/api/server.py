"""
src/api/server.py
Defense-grade FastAPI application with security middleware, RBAC routes,
structured JSON logging, and rate-limiter integration.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.security.auth import AuthManager, RateLimiter, SECURITY_HEADERS, SecurityConfig
from src.security.audit import AuditLedger
from src.api.routes import auth as auth_router
from src.api.routes import jobs as jobs_router
from src.api.routes import viewer as viewer_router

# ---------------------------------------------------------------------------
# Structured logging (JSON, no PII leakage)
# ---------------------------------------------------------------------------
logging.basicConfig(
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    level=logging.INFO,
)
logger = logging.getLogger("samanvaya")

# ---------------------------------------------------------------------------
# Global singletons (initialized in lifespan)
# ---------------------------------------------------------------------------
_auth_manager: AuthManager | None = None
_rate_limiter: RateLimiter | None = None
_audit_ledger: AuditLedger | None = None


from src.core.optimizer import HardwareOptimizer

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    global _auth_manager, _rate_limiter, _audit_ledger

    logger.info("Samanvaya API starting up")
    
    # -------------------------------------------------------------
    # Low-End PC Hardware Optimization Check
    # -------------------------------------------------------------
    HardwareOptimizer.apply_low_end_optimizations()
    
    _auth_manager = AuthManager(SecurityConfig())
    _rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
    _audit_ledger = AuditLedger(Path("data/audit/ledger.jsonl"))

    # Attach to app state for route access
    app.state.auth    = _auth_manager
    app.state.limiter = _rate_limiter
    app.state.audit   = _audit_ledger
    app.state.optimizer = HardwareOptimizer

    yield

    logger.info("Samanvaya API shutting down")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="Samanvaya Aerospace Registration API",
        version="2.0.0",
        description=(
            "Mission-critical, defense-grade lunar image registration platform "
            "for ISRO Chandrayaan-2 (OHRC, TMC-2, IIRS) optical payloads."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS (locked down — no wildcard in production)
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ------------------------------------------------------------------
    # Security headers + rate limiter middleware
    # ------------------------------------------------------------------
    @app.middleware("http")
    async def security_middleware(request: Request, call_next) -> Response:
        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        limiter: RateLimiter = getattr(request.app.state, "limiter", None)

        if limiter:
            # Auth endpoints: stricter limit (10/min)
            if request.url.path.startswith("/auth"):
                auth_limiter = RateLimiter(max_requests=10, window_seconds=60)
                if not auth_limiter.is_allowed(f"auth:{client_ip}"):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many authentication attempts"},
                    )
            elif not limiter.is_allowed(f"api:{client_ip}"):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )

        # Process request
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Inject security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Remove server fingerprinting headers
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # Structured access log (no query params / body to avoid PII)
        logger.info(
            f'method={request.method} path={request.url.path} '
            f'status={response.status_code} duration_ms={duration_ms} ip={client_ip}'
        )
        return response

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(auth_router.router,   prefix="/auth",   tags=["Authentication"])
    app.include_router(jobs_router.router,   prefix="/jobs",   tags=["Pipeline Jobs"])
    app.include_router(viewer_router.router, prefix="/viewer", tags=["Viewer & Export"])

    # ------------------------------------------------------------------
    # Health + audit chain verification endpoint
    # ------------------------------------------------------------------
    @app.get("/health", tags=["System"])
    async def health(request: Request) -> dict[str, Any]:
        audit: AuditLedger = request.app.state.audit
        chain_ok = audit.verify_chain()
        return {
            "status": "operational",
            "version": "2.0.0",
            "audit_chain_intact": chain_ok,
            "audit_entries": audit.chain_length(),
        }

    return app


app = create_app()
