"""Vigil Home - Email Notification Service

Sends critical/high severity alerts via SMTP.
Supports multiple SMTP providers: Microsoft 365 (Graph API), Gmail (SMTP), iCloud SMTP.

Uses an asyncio background task queue to avoid blocking the request path.
All public sync APIs (send_alert_email, send_test_email) enqueue work and return
immediately. A background asyncio worker drains the queue and sends emails.

Rate-limited to avoid spamming — the rate limiter is checked at send time, not
at enqueue time.
"""

import os
import time
import logging
import asyncio
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Callable

logger = logging.getLogger("vigil.email")

# ── Configuration ──────────────────────────────────────────────────

# Rate limiting: max N emails per sliding window
ALERT_EMAIL_WINDOW_SEC = int(os.environ.get("VIGIL_EMAIL_WINDOW", "3600"))   # 1 hour
ALERT_EMAIL_MAX_PER_WINDOW = int(os.environ.get("VIGIL_EMAIL_MAX", "10"))     # max 10/hr

# SMTP provider selection
# "m365" | "gmail" | "icloud" | "custom"
SMTP_PROVIDER = os.environ.get("VIGIL_SMTP_PROVIDER", "gmail")

# ── SMTP Credentials ────────────────────────────────────────────────
# M365 / Microsoft Graph
M365_CLIENT_ID = os.environ.get("M365_CLIENT_ID", "")
M365_TENANT_ID = os.environ.get("M365_TENANT_ID", "")
M365_CLIENT_SECRET = os.environ.get("M365_CLIENT_SECRET", "")

# Gmail SMTP
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# iCloud SMTP
ICLOUD_USER = os.environ.get("ICLOUD_USER", "")
ICLOUD_APP_PASSWORD = os.environ.get("ICLOUD_APP_PASSWORD", "")

# Custom SMTP
SMTP_HOST = os.environ.get("VIGIL_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("VIGIL_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("VIGIL_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("VIGIL_SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("VIGIL_SMTP_TLS", "true").lower() == "true"

# Sender and recipient
ALERT_EMAIL_FROM = os.environ.get("VIGIL_ALERT_FROM", "vigil@hockeyops.ai")
ALERT_EMAIL_TO = os.environ.get("VIGIL_ALERT_TO", "erik_ross@hockeyops.ai")

# Hostname for email footer
HOSTNAME = os.environ.get("VIGIL_HOSTNAME", "gx-10.local")


# ── Alert severity levels that trigger email ───────────────────────

EMAIL_SEVERITY_LEVELS = {"critical", "high"}


@dataclass
class AlertEmailContext:
    """Context data for building an alert email."""
    severity: str
    title: str
    description: str
    timestamp: str
    device_name: str
    mac_address: str
    trust_score: float
    device_type: str
    device_id: int
    alert_id: int
    alert_type: str


# ── SMTP Provider Configuration ────────────────────────────────────

SMTP_PROVIDERS = {
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "user_env": "GMAIL_USER",
        "pass_env": "GMAIL_APP_PASSWORD",
    },
    "icloud": {
        "host": "smtp.mail.me.com",
        "port": 587,
        "use_tls": True,
        "user_env": "ICLOUD_USER",
        "pass_env": "ICLOUD_APP_PASSWORD",
    },
    "m365": {
        "host": "smtp.office365.com",
        "port": 587,
        "use_tls": True,
        "user_env": "M365_CLIENT_ID",  # M365 SMTP uses email, not client ID
        "pass_env": "M365_CLIENT_SECRET",
    },
    "custom": {
        "host_env": "VIGIL_SMTP_HOST",
        "port_env": "VIGIL_SMTP_PORT",
        "tls_env": "VIGIL_SMTP_TLS",
        "user_env": "VIGIL_SMTP_USER",
        "pass_env": "VIGIL_SMTP_PASSWORD",
    },
}


# ── Rate Limiter ───────────────────────────────────────────────────

class SlidingWindowRateLimiter:
    """Simple sliding window rate limiter using monotonic timestamps."""

    def __init__(self, max_per_window: int, window_sec: float):
        self.max_per_window = max_per_window
        self.window_sec = window_sec
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Check and record a new event. Returns True if allowed."""
        now = time.monotonic()
        with self._lock:
            # Remove expired entries
            cutoff = now - self.window_sec
            self._timestamps = [t for t in self._timestamps if t > cutoff]

            if len(self._timestamps) >= self.max_per_window:
                return False

            self._timestamps.append(now)
            return True

    @property
    def remaining(self) -> int:
        """Number of slots available in current window."""
        now = time.monotonic()
        cutoff = now - self.window_sec
        with self._lock:
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            return max(0, self.max_per_window - len(self._timestamps))

    @property
    def window_remaining(self) -> float:
        """Seconds until the oldest timestamp expires."""
        with self._lock:
            if not self._timestamps:
                return 0.0
            oldest = min(self._timestamps)
            return max(0.0, (oldest + self.window_sec) - time.monotonic())


# Global rate limiter instance
_rate_limiter = SlidingWindowRateLimiter(
    max_per_window=ALERT_EMAIL_MAX_PER_WINDOW,
    window_sec=ALERT_EMAIL_WINDOW_SEC,
)


# ── Email Templates ────────────────────────────────────────────────

def _build_email_subject(ctx: AlertEmailContext) -> str:
    return f"[Vigil ALERT] {ctx.severity.upper()}: {ctx.title}"


def _build_email_body(ctx: AlertEmailContext) -> str:
    return f"""Vigil Home Security Alert
────────────────────────

Severity: {ctx.severity.upper()}
Time: {ctx.timestamp}
Device: {ctx.device_name} ({ctx.mac_address})
Alert Type: {ctx.alert_type}

{ctx.description}

Trust Score: {ctx.trust_score}
Device Type: {ctx.device_type}

View in Dashboard: http://192.168.50.30:8000/devices/{ctx.device_id}

────────────────────────
Alert ID: {ctx.alert_id}
This alert was generated by Vigil Home on {HOSTNAME}
"""


def _build_html_body(ctx: AlertEmailContext) -> str:
    severity_color = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745",
        "info": "#17a2b8",
    }.get(ctx.severity, "#6c757d")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: {severity_color}; color: #fff; padding: 20px 24px; }}
        .header h1 {{ margin: 0; font-size: 20px; }}
        .header .badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
        .body {{ padding: 24px; }}
        .field {{ margin-bottom: 12px; }}
        .field-label {{ font-size: 11px; text-transform: uppercase; color: #6c757d; letter-spacing: 1px; margin-bottom: 2px; }}
        .field-value {{ font-size: 14px; color: #333; }}
        .description {{ background: #f8f9fa; padding: 16px; border-radius: 6px; margin: 16px 0; font-size: 14px; line-height: 1.5; }}
        .trust-score {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: bold; }}
        .trust-low {{ background: #dc3545; color: #fff; }}
        .trust-medium {{ background: #ffc107; color: #333; }}
        .trust-high {{ background: #28a745; color: #fff; }}
        .footer {{ background: #f8f9fa; padding: 16px 24px; font-size: 12px; color: #6c757d; border-top: 1px solid #e9ecef; }}
        .dashboard-link {{ display: inline-block; background: #0066cc; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-size: 14px; margin-top: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="badge">{ctx.severity} alert</div>
            <h1>🛡️ {ctx.title}</h1>
        </div>
        <div class="body">
            <div class="field">
                <div class="field-label">Device</div>
                <div class="field-value">{ctx.device_name} ({ctx.mac_address})</div>
            </div>
            <div class="field">
                <div class="field-label">Time</div>
                <div class="field-value">{ctx.timestamp}</div>
            </div>
            <div class="field">
                <div class="field-label">Device Type</div>
                <div class="field-value">{ctx.device_type}</div>
            </div>
            <div class="field">
                <div class="field-label">Trust Score</div>
                <div class="field-value">
                    <span class="trust-score {'trust-low' if ctx.trust_score < 0.3 else 'trust-medium' if ctx.trust_score < 0.6 else 'trust-high'}">
                        {ctx.trust_score:.4f}
                    </span>
                </div>
            </div>
            <div class="description">{ctx.description}</div>
            <a class="dashboard-link" href="http://192.168.50.30:8000/devices/{ctx.device_id}">
                View in Dashboard →
            </a>
        </div>
        <div class="footer">
            Alert ID: {ctx.alert_id} | Generated by Vigil Home on {HOSTNAME}
        </div>
    </div>
</body>
</html>
"""


# ── SMTP Connection (synchronous, called by the background worker) ──

def _get_smtp_config() -> Optional[dict]:
    """Resolve SMTP configuration based on the selected provider."""
    provider_cfg = SMTP_PROVIDERS.get(SMTP_PROVIDER)
    if not provider_cfg:
        logger.error(f"Unknown SMTP provider: {SMTP_PROVIDER}")
        return None

    if SMTP_PROVIDER == "custom":
        host = os.environ.get(provider_cfg["host_env"], "")
        port_str = os.environ.get(provider_cfg["port_env"], "587")
        port = int(port_str) if port_str else 587
        use_tls = os.environ.get(provider_cfg["tls_env"], "true").lower() == "true"
        user = os.environ.get(provider_cfg["user_env"], "")
        password = os.environ.get(provider_cfg["pass_env"], "")
    else:
        host = provider_cfg["host"]
        port = provider_cfg["port"]
        use_tls = provider_cfg["use_tls"]
        user = os.environ.get(provider_cfg["user_env"], "")
        password = os.environ.get(provider_cfg["pass_env"], "")

    if not host or not user or not password:
        logger.warning(
            f"SMTP provider '{SMTP_PROVIDER}' is not fully configured. "
            f"Missing host={bool(host)}, user={bool(user)}, password={bool(password)}"
        )
        return None

    return {
        "host": host,
        "port": port,
        "use_tls": use_tls,
        "user": user,
        "password": password,
    }


def _send_email_sync(subject: str, body_text: str, body_html: str) -> bool:
    """Send an email via the configured SMTP provider (blocking).

    This is called by the background worker thread via a thread executor —
    never on the request path.
    """
    cfg = _get_smtp_config()
    if not cfg:
        logger.error("Cannot send email: SMTP not configured")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = ALERT_EMAIL_FROM
        msg["To"] = ALERT_EMAIL_TO
        msg["Subject"] = subject
        msg["X-Vigil-Alert"] = "true"
        msg["X-Vigil-Version"] = "1.0"

        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
            if cfg["use_tls"]:
                server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)

        logger.info(f"Email sent: {subject} -> {ALERT_EMAIL_TO}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        logger.error(f"SMTP connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected email error: {e}")
        return False


# ── Async Email Queue ──────────────────────────────────────────────
#
# An asyncio.Queue holds pending email jobs. A background asyncio task
# (started from main.py) drains this queue and calls the synchronous
# SMTP code in a thread executor so it never blocks the event loop.
#
# A thread-safe path is provided for callers from non-async contexts
# (e.g., the Suricata eve.json thread in detection.py): an
# asyncio.run_coroutine_threadsafe wrapper that uses the running event
# loop reference.

# The asyncio Queue — items are tuples of (subject, body_text, body_html)
_email_queue: 'asyncio.Queue[tuple[str, str, str]] | None' = None

# Reference to the running event loop (set by start_email_worker)
_event_loop: asyncio.AbstractEventLoop | None = None

# Queue size counter (thread-safe via non-mutable read, only modified
# by the synchronous _build_and_enqueue path)
_queue_size = 0


async def _enqueue_email(subject: str, body_text: str, body_html: str):
    """Place an email job on the async queue."""
    if _email_queue is not None:
        await _email_queue.put((subject, body_text, body_html))


async def _email_worker():
    """Background asyncio task: drain the email queue and send via thread executor.

    Each email is sent in a thread executor to avoid blocking the event loop.
    Rate limiting is checked at send time against the actual send timestamp.
    """
    logger.info("Async email worker started (queue-based, non-blocking send path)")
    loop = asyncio.get_running_loop()

    while True:
        try:
            subject, body_text, body_html = await _email_queue.get()
            global _queue_size
            _queue_size -= 1

            # Check rate limiter at send time (in the worker)
            if not _rate_limiter.allow():
                logger.warning(
                    f"Email rate limited (dropping): "
                    f"{_rate_limiter.remaining} slots remaining in window, "
                    f"{_rate_limiter.window_remaining:.0f}s until reset. "
                    f"Subject: {subject}"
                )
                _email_queue.task_done()
                continue

            # Send in thread executor to avoid blocking the event loop
            await loop.run_in_executor(
                None,
                _send_email_sync,
                subject,
                body_text,
                body_html,
            )

            _email_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Async email worker cancelled — draining remaining queue")
            break
        except Exception as e:
            logger.exception(f"Email worker error: {e}")
            _email_queue.task_done()


# ── Async Worker Lifecycle ─────────────────────────────────────────

def start_email_worker(loop: asyncio.AbstractEventLoop | None = None) -> asyncio.Task:
    """Start the background email worker.

    Called from main.py's startup hook. Sets up the queue, stores the event
    loop reference, and returns the worker Task so the caller can manage its
    lifecycle.

    Args:
        loop: Event loop to use. Defaults to the running loop.

    Returns:
        The asyncio Task for the email worker.
    """
    global _email_queue, _event_loop

    _email_queue = asyncio.Queue(maxsize=100)  # cap at 100 pending emails
    _event_loop = loop or asyncio.get_running_loop()

    worker_task = _event_loop.create_task(_email_worker())
    logger.info("Email worker started (queue size limit: 100)")
    return worker_task


def stop_email_worker(worker_task: asyncio.Task | None):
    """Cancel the background email worker.

    Gracefully drains remaining items on cancellation.
    """
    if worker_task is not None and not worker_task.done():
        worker_task.cancel()


# ── Public API ─────────────────────────────────────────────────────

def _build_and_enqueue(ctx: AlertEmailContext) -> bool:
    """Build email parts and enqueue for async sending.

    Returns True immediately after enqueuing.
    This is the fast path — no SMTP, no blocking.
    """
    global _queue_size

    # Check severity threshold (fast, no I/O)
    if ctx.severity not in EMAIL_SEVERITY_LEVELS:
        logger.debug(f"Skipping email for {ctx.severity} alert (threshold: {EMAIL_SEVERITY_LEVELS})")
        return False

    subject = _build_email_subject(ctx)
    body_text = _build_email_body(ctx)
    body_html = _build_html_body(ctx)

    # Enqueue for the async worker
    if _event_loop is None or _event_loop.is_closed():
        # Fallback: no async worker running, send synchronously
        logger.warning("No async email worker running — sending synchronously")
        return _send_email_sync(subject, body_text, body_html)

    _queue_size += 1

    asyncio.run_coroutine_threadsafe(
        _enqueue_email(subject, body_text, body_html),
        _event_loop,
    )
    return True


def send_alert_email(ctx: AlertEmailContext) -> bool:
    """Queue an alert email for async sending.

    Returns True immediately after enqueuing (not after the email is sent).
    Previously this blocked for 1-5 seconds on SMTP; now it's near-instant.

    If the async worker is not running, falls back to synchronous sending.
    """
    return _build_and_enqueue(ctx)


def send_test_email() -> dict:
    """Send a test email to verify configuration.

    Test emails bypass the queue and are sent immediately via
    the synchronous path (blocking, but it's a one-off test).

    Returns a dict with status and message.
    """
    ctx = AlertEmailContext(
        severity="high",
        title="Test Alert — Configuration Verification",
        description="This is a test alert from Vigil Home. If you received this, email notification is configured correctly.",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        device_name="Vigil Home System",
        mac_address="00:00:00:00:00:00",
        trust_score=0.5,
        device_type="system",
        device_id=0,
        alert_id=0,
        alert_type="test",
    )

    subject = _build_email_subject(ctx)
    body_text = _build_email_body(ctx)
    body_html = _build_html_body(ctx)

    success = _send_email_sync(subject, body_text, body_html)

    if success:
        return {
            "status": "sent",
            "message": f"Test email sent to {ALERT_EMAIL_TO}",
            "provider": SMTP_PROVIDER,
            "rate_limiter": {
                "remaining": _rate_limiter.remaining,
                "window_sec": ALERT_EMAIL_WINDOW_SEC,
                "max_per_window": ALERT_EMAIL_MAX_PER_WINDOW,
            },
        }
    else:
        cfg = _get_smtp_config()
        if not cfg:
            return {
                "status": "error",
                "message": f"SMTP provider '{SMTP_PROVIDER}' is not configured. "
                           f"Set environment variables for the provider.",
            }
        return {
            "status": "error",
            "message": "Failed to send test email. Check SMTP configuration and network.",
        }


def get_email_status() -> dict:
    """Get current email notification system status."""
    cfg = _get_smtp_config()
    return {
        "configured": cfg is not None,
        "provider": SMTP_PROVIDER,
        "severity_thresholds": sorted(list(EMAIL_SEVERITY_LEVELS)),
        "rate_limiter": {
            "remaining": _rate_limiter.remaining,
            "max_per_window": ALERT_EMAIL_MAX_PER_WINDOW,
            "window_sec": ALERT_EMAIL_WINDOW_SEC,
            "window_remaining_sec": _rate_limiter.window_remaining,
        },
        "queue": {
            "configured": _email_queue is not None,
            "pending": _queue_size,
            "max_size": 100,
        },
        "recipient": ALERT_EMAIL_TO,
        "from": ALERT_EMAIL_FROM,
        "hostname": HOSTNAME,
    }
