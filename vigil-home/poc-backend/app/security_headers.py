"""Vigil Home — Security Headers Middleware

Adds security-focused HTTP headers to all responses:
- X-Content-Type-Options: nosniff (prevent MIME sniffing)
- X-Frame-Options: DENY (prevent clickjacking)
- X-XSS-Protection: 1; mode=block (legacy XSS filter)
- Content-Security-Policy: default-src 'self' (restrict resource loading)
- Strict-Transport-Security: max-age=31536000 (HSTS)
- Cache-Control: no-store (prevent sensitive data caching)

Per SECURITY-HARDENING-PLAN.md Phase 2.
"""

from fastapi import Request
from fastapi.responses import Response
from typing import Callable


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """Add security headers to all responses.

    This middleware runs after the route handler, so it can modify
    the response before it's sent to the client.
    """
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking (deny all framing)
    response.headers["X-Frame-Options"] = "DENY"

    # Legacy XSS filter (mostly obsolete but harmless)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy - restrict resource loading
    # For an API backend, we're restrictive but allow:
    # - Same-origin for everything
    # - Data URIs for images (common in dashboards)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )

    # HSTS - enforce HTTPS for 1 year (only if not localhost)
    # Skip for localhost/development to avoid certificate issues
    host = request.headers.get("host", "")
    if not host.startswith("localhost") and not host.startswith("127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Prevent caching of API responses (contains sensitive data)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    return response
