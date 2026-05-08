# One-Line Deploy: Vigil Email Alerting

## Prerequisites
- SSH access to GX-10 (192.168.50.30)
- Docker and docker-compose installed on GX-10
- Git access to https://github.com/Kosfootel/agent-woodhouse

## Deploy

SSH into GX-10 and run:

```bash
cd /opt/vigil && \
git clone --depth 1 https://github.com/Kosfootel/agent-woodhouse.git /tmp/woodhouse-update && \
cp /tmp/woodhouse-update/projects/vigil-home/poc-backend/app/email_notifier.py app/ && \
cp /tmp/woodhouse-update/projects/vigil-home/poc-backend/app/email_poller.py app/ && \
cp /tmp/woodhouse-update/projects/vigil-home/poc-backend/app/detection.py app/ && \
cp /tmp/woodhouse-update/projects/vigil-home/poc-backend/app/main.py app/ && \
cp /tmp/woodhouse-update/projects/vigil-home/poc-backend/docker-compose.yml ./ && \
rm -rf /tmp/woodhouse-update && \
docker compose down && docker compose up -d && \
echo "Waiting for container..." && sleep 3 && \
echo "Status:" && curl -s http://localhost:8000/email/status | python3 -m json.tool && \
echo "" && echo "Sending test email..." && curl -s http://localhost:8000/email/test | python3 -m json.tool
```

## Verify

After deploy, check:

1. **Email status endpoint:** `curl http://192.168.50.30:8000/email/status`
2. **Test email:** `curl http://192.168.50.30:8000/email/test` — check erik_ross@hockeyops.ai inbox
3. **Email poller logs:** `docker compose logs -f vigil-email-poller`

## Manual (if git not available)

From GX-10 terminal:

```bash
cd /opt/vigil

# Create the email notifier module
cat > app/email_notifier.py << 'PYEOF'
# [Paste contents of app/email_notifier.py here]
PYEOF

# Create the email poller
cat > app/email_poller.py << 'PYEOF'
# [Paste contents of app/email_poller.py here]
PYEOF

# Copy updated files (have these ready)
cp /path/to/updated/detection.py app/
cp /path/to/updated/main.py app/
cp /path/to/updated/docker-compose.yml ./

# Restart
docker compose down && docker compose up -d
```
