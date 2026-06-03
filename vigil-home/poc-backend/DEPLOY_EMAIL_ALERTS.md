# Deploy Email Alerting for Vigil Home

## Overview

Adds email notification for critical/high severity security alerts detected by Vigil Home.
Emails are sent to `erik_ross@hockeyops.ai` via Gmail SMTP.

## What's Included

1. **`app/email_notifier.py`** — Email notification module with:
   - SMTP support for Gmail, iCloud, M365, or custom servers
   - Rate limiting (max 10 emails/hour, configurable)
   - Rich HTML email templates with severity-colored headers
   - Plain-text email fallback
   - Test endpoint (`GET /email/test`)

2. **`app/email_poller.py`** — Standalone poller service (optional)
   - Runs as a separate container monitoring the Vigil API
   - Processes historical alerts on startup
   - Persists last-processed alert ID across restarts

3. **API Endpoints** (added to main.py):
   - `GET /email/status` — Check email configuration status
   - `GET /email/test` — Send a test email
   - `POST /email/send-alert?alert_id=N` — Manually email a specific alert

4. **Auto-send Integration** — Email is sent automatically when:
   - Suricata generates a critical/high alert (in `detection.py`)
   - Manual event ingestion creates a critical/high alert (in `main.py`)

## Alert Thresholds (Severity → Email)

| Severity | Email Sent? |
|----------|-------------|
| CRITICAL | ✅ Yes |
| HIGH     | ✅ Yes |
| MEDIUM   | ❌ No |
| LOW      | ❌ No |
| INFO     | ❌ No |

### Alert Types That Trigger Email

- [CRITICAL] New unknown device with suspicious behaviour
- [CRITICAL] Port scanning detected
- [CRITICAL] Device trust score drops below 0.2
- [HIGH] Multiple failed authentication attempts
- [HIGH] Unusual outbound connection patterns
- Any Suricata alert classified as critical/high

## Deployment

### Option A: Quick Deploy (copy files into running container)

```bash
# Copy the new email module into the api container
docker cp app/email_notifier.py vigil-home-api:/app/app/email_notifier.py

# Copy updated detection.py and main.py into the container
docker cp app/detection.py vigil-home-api:/app/app/detection.py
docker cp app/main.py vigil-home-api:/app/app/main.py

# Restart the api container
docker restart vigil-home-api

# Test email configuration
curl http://localhost:8000/email/test
```

### Option B: Full rebuild with docker-compose

```bash
# On GX-10, from /opt/vigil/
cd /opt/vigil/

# Pull latest code (if pushed to GitHub)
# OR copy the files from this deploy package

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d

# Verify
curl http://localhost:8000/email/status
```

### Option C: Deploy email poller as separate container

```bash
# After updating docker-compose.yml, rebuild and start
docker compose up -d vigil-email-poller

# Check logs
docker compose logs -f vigil-email-poller
```

## Verification

1. **Check email status:**
   ```bash
   curl http://192.168.50.30:8000/email/status
   ```

2. **Send test email:**
   ```bash
   curl http://192.168.50.30:8000/email/test
   # Check erik_ross@hockeyops.ai inbox
   ```

3. **Trigger a test alert:**
   ```bash
   curl -X POST http://192.168.50.30:8000/events \
     -H "Content-Type: application/json" \
     -d '{
       "device_id": 1,
       "event_type": "scan_detected",
       "severity": "critical",
       "value": 999.0,
       "details": {"source": "external", "ports": [22, 80, 443]}
     }'
   ```

4. **Send existing alert via email:**
   ```bash
   curl -X POST "http://192.168.50.30:8000/email/send-alert?alert_id=1"
   ```

## SMTP Configuration

Edit environment variables in `docker-compose.yml` or pass at runtime:

| Variable | Description | Default |
|----------|-------------|---------|
| `VIGIL_SMTP_PROVIDER` | SMTP provider: `gmail`, `icloud`, `m365`, `custom` | `gmail` |
| `GMAIL_USER` | Gmail address | `kosfootel@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail app password | (pre-configured) |
| `VIGIL_ALERT_TO` | Recipient email | `erik_ross@hockeyops.ai` |
| `VIGIL_ALERT_FROM` | Sender email | `vigil@hockeyops.ai` |
| `VIGIL_EMAIL_WINDOW` | Rate limit window (seconds) | `3600` (1 hour) |
| `VIGIL_EMAIL_MAX` | Max emails per window | `10` |
| `VIGIL_HOSTNAME` | Hostname in email footer | `gx-10.local` |

### Switching to iCloud SMTP

```yaml
environment:
  - VIGIL_SMTP_PROVIDER=icloud
  - ICLOUD_USER=erikdross@me.com
  - ICLOUD_APP_PASSWORD=your-app-password
```

### Switching to M365 SMTP

```yaml
environment:
  - VIGIL_SMTP_PROVIDER=m365
  - M365_CLIENT_ID=erik_ross@hockeyops.ai
  - M365_CLIENT_SECRET=your-password
```

## Email Template

```
Subject: [Vigil ALERT] CRITICAL: Port Scanning Detected

Vigil Home Security Alert
────────────────────────

Severity: CRITICAL
Time: 2026-05-07 22:00:00 UTC
Device: MacBook-Pro (AA:BB:CC:DD:EE:FF)

External host 10.0.0.99 scanning ports 22,80,443 on MacBook-Pro.
Anomaly detected: 999 connections in 60 seconds (z=12.4)

Trust Score: 0.2150
Device Type: computer

View in Dashboard: http://192.168.50.30:8000/devices/42

────────────────────────
Alert ID: 7
This alert was generated by Vigil Home on gx-10.local
```

HTML version includes severity-colored header and dashboard link button.
