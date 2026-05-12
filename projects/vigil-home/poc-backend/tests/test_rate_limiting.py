"""Tests for Vigil Home rate limiting.

Tests the rate_limiter module configuration, limit presets, and
decorator coverage on all main.py endpoint functions.

Rate-limit-enforcement tests (429 behaviour) use isolated Limiter
instances so in-memory counters don't bleed between tests.
"""

import os
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.rate_limiter import (
    AUTH_LIMITS,
    SSE_LIMITS,
    GENERAL_LIMITS,
    EMAIL_SEND_LIMITS,
    configure_rate_limiting,
)


# ── Helpers ────────────────────────────────────────────────────────


def _isolated_limiter() -> Limiter:
    """Return a fresh, enabled Limiter with no default limits."""
    return Limiter(key_func=get_remote_address, default_limits=[], enabled=True)


def _make_app(lim: Limiter | None = None) -> FastAPI:
    """Create a FastAPI app with rate limiting configured."""
    app = FastAPI()
    configure_rate_limiting(app, limiter_override=lim)
    return app


# ── Tests: Limit presets ───────────────────────────────────────────


class TestRateLimitConstants:
    """Verify the rate limit presets are sensible."""

    def test_auth_limits_are_strict(self):
        assert "5/minute" in AUTH_LIMITS
        assert "20/hour" in AUTH_LIMITS

    def test_sse_limits_are_moderate(self):
        assert "10/minute" in SSE_LIMITS
        assert "120/hour" in SSE_LIMITS

    def test_general_limits_have_burst_and_window(self):
        assert "60/minute" in GENERAL_LIMITS
        assert "600/hour" in GENERAL_LIMITS

    def test_email_send_limits_are_stricter(self):
        assert "10/minute" in EMAIL_SEND_LIMITS
        assert "60/hour" in EMAIL_SEND_LIMITS

    def test_auth_stricter_than_general(self):
        auth = int(AUTH_LIMITS.split(";")[0].split("/")[0].strip())
        gen = int(GENERAL_LIMITS.split(";")[0].split("/")[0].strip())
        assert auth < gen

    def test_sse_limits_between_auth_and_general(self):
        auth = int(AUTH_LIMITS.split(";")[0].split("/")[0].strip())
        sse = int(SSE_LIMITS.split(";")[0].split("/")[0].strip())
        gen = int(GENERAL_LIMITS.split(";")[0].split("/")[0].strip())
        assert auth < sse < gen


# ── Tests: Auth endpoint limits (5/min) ────────────────────────────


class TestAuthRateLimiting:
    """Auth endpoints should enforce 5/minute."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        lim = _isolated_limiter()
        self.app = _make_app(lim)

        @self.app.post("/auth/login")
        @lim.limit(AUTH_LIMITS)
        def login(request: Request):
            return {"access_token": "mock"}

        self.client = TestClient(self.app)

    def test_allows_5_per_minute(self):
        for i in range(5):
            resp = self.client.post("/auth/login")
            assert resp.status_code == 200, f"Request {i+1} failed"

    def test_blocks_6th_request(self):
        for _ in range(5):
            self.client.post("/auth/login")
        resp = self.client.post("/auth/login")
        assert resp.status_code == 429

    def test_separate_routes_have_separate_buckets(self):
        """Hitting /login 5 times shouldn't affect /refresh."""
        lim = _isolated_limiter()
        app = _make_app(lim)
        @app.post("/auth/login")
        @lim.limit(AUTH_LIMITS)
        def login(request: Request): return {"access_token": "mock"}
        @app.post("/auth/refresh")
        @lim.limit(AUTH_LIMITS)
        def refresh(request: Request): return {"access_token": "mock"}
        client = TestClient(app)
        for _ in range(5):
            client.post("/auth/login")
        resp = client.post("/auth/refresh")
        assert resp.status_code == 200


# ── Tests: SSE endpoint limits (10/min) ────────────────────────────


class TestSSERateLimiting:
    """SSE stream should enforce 10/minute."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        lim = _isolated_limiter()
        self.app = _make_app(lim)

        @self.app.get("/events/stream")
        @lim.limit(SSE_LIMITS)
        async def stream(request: Request):
            from fastapi.responses import StreamingResponse

            async def _gen():
                yield b"data: test\n\n"

            return StreamingResponse(_gen(), media_type="text/event-stream")

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_allows_10_then_blocks_11th(self):
        for i in range(10):
            resp = self.client.get("/events/stream")
            assert resp.status_code == 200, f"Request {i+1} got {resp.status_code}"
        resp = self.client.get("/events/stream")
        assert resp.status_code == 429


# ── Tests: General API limits (60/min) ─────────────────────────────


class TestGeneralRateLimiting:
    """General API should enforce 60/minute."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        lim = _isolated_limiter()
        self.app = _make_app(lim)

        @self.app.get("/devices")
        @lim.limit(GENERAL_LIMITS)
        def devices(request: Request):
            return {"devices": []}

        self.client = TestClient(self.app)

    def test_allows_60_then_blocks_61st(self):
        for i in range(60):
            resp = self.client.get("/devices")
            assert resp.status_code == 200, f"Request {i+1} got {resp.status_code}"
        resp = self.client.get("/devices")
        assert resp.status_code == 429


# ── Tests: Email send limits (10/min) ──────────────────────────────


class TestEmailSendRateLimiting:
    """Email send endpoints should enforce 10/minute."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        lim = _isolated_limiter()
        self.app = _make_app(lim)

        @self.app.get("/email/test")
        @lim.limit(EMAIL_SEND_LIMITS)
        def email_test(request: Request):
            return {"status": "ok"}

        self.client = TestClient(self.app)

    def test_allows_10_then_blocks_11th(self):
        for i in range(10):
            resp = self.client.get("/email/test")
            assert resp.status_code == 200, f"Request {i+1} got {resp.status_code}"
        resp = self.client.get("/email/test")
        assert resp.status_code == 429


# ── Tests: Health endpoint (no limit) ──────────────────────────────


class TestHealthNoLimit:
    """Health endpoint should not be rate-limited."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.app = _make_app()
        @self.app.get("/health")
        def health(request: Request):
            return {"status": "ok"}
        self.client = TestClient(self.app)

    def test_never_rate_limited(self):
        for i in range(100):
            resp = self.client.get("/health")
            assert resp.status_code == 200, f"Request {i+1} failed at {resp.status_code}"


# ── Tests: Limiter configuration ───────────────────────────────────


class TestLimiterConfig:
    """Verify the module-level limiter and configuration utility."""

    def test_module_level_limiter_is_limiter(self):
        from app.rate_limiter import limiter as module_limiter
        assert isinstance(module_limiter, Limiter)

    def test_configure_rate_limiting_adds_limiter_to_state(self):
        app = FastAPI()
        configure_rate_limiting(app)
        assert hasattr(app.state, "limiter")

    def test_configure_rate_limiting_with_override(self):
        fresh = _isolated_limiter()
        app = FastAPI()
        configure_rate_limiting(app, limiter_override=fresh)
        assert app.state.limiter is fresh

    def test_key_func_extracts_x_forwarded_for(self):
        from app.rate_limiter import _key_func
        from unittest.mock import MagicMock

        req = MagicMock()
        req.headers.get.return_value = "203.0.113.5, 10.0.0.1"
        req.client.host = "10.0.0.1"

        key = _key_func(req)
        assert key == "203.0.113.5"

    def test_key_func_falls_back_to_remote_addr(self):
        from unittest.mock import MagicMock
        req = MagicMock()
        req.headers.get.return_value = None
        req.client.host = "192.168.1.100"
        addr = get_remote_address(req)
        assert addr == "192.168.1.100"


# ── Tests: 429 error response body ────────────────────────────────


class TestRateLimitExceeded:
    """RateLimitExceeded should return 429 with a proper JSON body."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        lim = _isolated_limiter()
        self.app = _make_app(lim)

        @self.app.get("/sensitive")
        @lim.limit("1/minute")
        def sensitive(request: Request):
            return {"ok": True}

        self.client = TestClient(self.app)

    def test_exceeded_returns_429(self):
        resp1 = self.client.get("/sensitive")
        assert resp1.status_code == 200
        resp2 = self.client.get("/sensitive")
        assert resp2.status_code == 429

    def test_exceeded_body_contains_error_field(self):
        self.client.get("/sensitive")
        resp = self.client.get("/sensitive")
        body = resp.json()
        assert "error" in body, f"Body keys: {list(body.keys())}"


# ── Tests: Main app decorator coverage ─────────────────────────────


class TestMainAppDecorators:
    """Static analysis: every route in main.py except /health should
    have @limiter.limit(...)."""

    def _routes(self):
        import ast
        main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(main_path) as f:
            tree = ast.parse(f.read())
        routes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                route_path = None
                has_limiter = False
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        fn = dec.func
                        if isinstance(fn.value, ast.Name) and fn.value.id == "app":
                            if fn.attr in ("get", "post", "patch", "delete", "put"):
                                if dec.args:
                                    pv = dec.args[0]
                                    if hasattr(pv, "value"):
                                        route_path = pv.value
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr == "limit":
                            val = dec.func.value
                            if isinstance(val, ast.Name) and val.id == "limiter":
                                has_limiter = True
                            if (isinstance(val, ast.Attribute)
                                    and val.attr == "limiter"):
                                has_limiter = True
                if route_path:
                    routes.append((node.name, route_path, has_limiter))
        return routes

    def test_all_endpoints_have_limiter(self):
        routes = self._routes()
        bad = [(n, p) for n, p, l in routes if not l and p != "/health"]
        assert not bad, (
            "Routes missing @limiter.limit:\n"
            + "\n".join(f"  {n} @ {p}" for n, p in bad)
        )

    def test_health_excluded(self):
        routes = self._routes()
        for _, path, has_lim in routes:
            if path == "/health":
                assert not has_lim, "/health should NOT have a limiter decorator"
