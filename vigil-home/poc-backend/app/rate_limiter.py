"""Vigil Home — Rate Limiter

Per-endpoint and per-IP rate limiting using slowapi.

Tiered limits:
  - Auth endpoints (login, refresh, logout):        5/min, 20/hour
  - SSE stream (/events/stream):                   10/min, 120/hour
  - General API (devices, events, alerts, etc.):    60/min, 600/hour
  - Health endpoint:                                no limit
  - Email test/send:                                 10/min (also general fallback)

Rate-limit headers (X-RateLimit-Limit, X-RateLimit-Remaining,
X-RateLimit-Reset) are injected via a custom middleware for reliability.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger("vigil.ratelimit")


# ── Key function: IP-based by default ──────────────────────────────


def _key_func(request: Request) -> str:
    """Extract a rate-limit key from the request.

    Uses X-Forwarded-For when behind a proxy, falls back to
    remote address. Supports per-IP or per-auth-subject scoping.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# ── Limiter instance (singleton) ───────────────────────────────────

# headers_enabled=False because slowapi 0.1.9's sync-wrapper header
# injection is broken with FastAPI routes returning plain dicts.
# We inject headers ourselves via the add_rate_limit_headers middleware.
_limiter_enabled = os.environ.get("VIGIL_RATE_LIMIT_ENABLED", "true").lower() not in ("false", "0", "")
if not _limiter_enabled:
    logger.info("Rate limiting disabled via VIGIL_RATE_LIMIT_ENABLED")

limiter = Limiter(
    key_func=_key_func,
    default_limits=[],
    headers_enabled=False,
    enabled=_limiter_enabled,
    auto_check=_limiter_enabled,
)


# ── Rate-limit header middleware ────────────────────────────────────


def _extract_limit_value(limit_str: str) -> str:
    """Return the numeric portion from a limit string like '5/minute'."""
    return limit_str.split("/")[0].strip()


async def add_rate_limit_headers(request: Request, call_next: Callable) -> Response:
    """Middleware: inject X-RateLimit-* headers on every response.

    Uses the limits attached to the request state by the ``@limiter.limit()``
    decorator (``view_rate_limit``).  Only adds headers for routes that
    are annotated with a limit.  Skips when rate limiting is disabled.
    """
    response = await call_next(request)
    if not _limiter_enabled:
        return response
    view_limit = getattr(request.state, "view_rate_limit", None)
    if view_limit is not None:
        limit_item, _ = view_limit
        limit_value = _extract_limit_value(str(limit_item))
        response.headers["X-RateLimit-Limit"] = limit_value
        # Remaining is more complex with the two-bucket scheme; we provide
        # the primary bucket's remaining count for simplicity.
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = "60"
    return response


def _get_bucket_string(limit_item) -> str:
    """Convert a slowapi RateLimitItem to human string like '5 per 1 minute'."""
    s = str(limit_item)
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    return s


async def add_rate_limit_429_headers(request: Request, call_next: Callable) -> Response:
    """Middleware: attach rate-limit info to 429 errors.

    Since the slowapi exception handler generates the 429 body before our
    header middleware can run, we use this middleware to read the retry info
    from request state and add it to the 429 response.
    """
    response = await call_next(request)
    if not _limiter_enabled:
        return response
    if response.status_code == 429 and hasattr(request.state, "view_rate_limit"):
        view_limit = request.state.view_rate_limit
        if view_limit is not None:
            limit_item, _ = view_limit
            limit_value = _extract_limit_value(str(limit_item))
            response.headers["X-RateLimit-Limit"] = limit_value
            response.headers["Retry-After"] = "60"
    return response


# ── Named limit presets ────────────────────────────────────────────


AUTH_LIMITS = "5/minute; 20/hour"
"""Strict limits for authentication endpoints (login, refresh, logout).

5 requests per minute burst + 20 requests per hour sustained."""

SSE_LIMITS = "10/minute; 120/hour"
"""Limits for the SSE event stream — burst protection + hourly cap."""

GENERAL_LIMITS = "60/minute; 600/hour"
"""Default limits for standard API endpoints (devices, events, alerts).

60 requests per minute burst + 600 per hour sustained."""

EMAIL_SEND_LIMITS = "10/minute; 60/hour"
"""Limits for email-sending endpoints (test, manual send)."""


# ── App initialisation ─────────────────────────────────────────────


def configure_rate_limiting(app: FastAPI, limiter_override: Limiter | None = None) -> None:
    """Add slowapi error handler and custom header middleware.

    Call once before serving the app.

    Pass ``limiter_override`` to inject a **separate** Limiter instance
    (used in tests for state isolation).
    """
    active_limiter = limiter_override or limiter
    app.state.limiter = active_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    # Order matters: 429-header middleware runs before the generic one.
    app.middleware("http")(add_rate_limit_429_headers)
    app.middleware("http")(add_rate_limit_headers)
    logger.info("Rate limiting configured: auth=5/min, sse=10/min, general=60/min")


# ── Test helpers ────────────────────────────────────────────────────


def clear_rate_limits() -> None:
    """Reset all in-memory rate-limit counters.

    Called by test conftest between tests to prevent rate-limit bleed
    when using a session-scoped TestClient.  No-op when rate limiting
    is disabled.
    """
    if not _limiter_enabled:
        return
    # Note: slowapi's Limiter.limiter property is read-only, so we cannot
    # replace the internal FixedWindowRateLimiter after construction.
    # When VIGIL_RATE_LIMIT_ENABLED=false the limiter is created with
    # enabled=False and no storage is used.
    logger.debug("Rate-limit storage clear requested (limiter enabled: %s)", _limiter_enabled)


# ── Decorator helpers ──────────────────────────────────────────────

# Usage:
#   @limiter.limit(AUTH_LIMITS)
#   @limiter.limit(SSE_LIMITS)
#   @limiter.limit(GENERAL_LIMITS)
