#!/bin/bash
# Deploy Email Alerting for Vigil Home
# Run this on GX-10 (192.168.50.30) in /opt/vigil/
# Usage: bash deploy-email.sh

set -euo pipefail

VIGIL_DIR="/opt/vigil"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$VIGIL_DIR/backups/$TIMESTAMP"

echo "=== Vigil Home Email Alerting Deploy ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# 1. Backup existing files
echo "[1/5] Backing up existing files..."
mkdir -p "$BACKUP_DIR"
[ -f "$VIGIL_DIR/app/detection.py" ] && cp "$VIGIL_DIR/app/detection.py" "$BACKUP_DIR/"
[ -f "$VIGIL_DIR/app/main.py" ] && cp "$VIGIL_DIR/app/main.py" "$BACKUP_DIR/"
[ -f "$VIGIL_DIR/docker-compose.yml" ] && cp "$VIGIL_DIR/docker-compose.yml" "$BACKUP_DIR/"
echo "  Backed up to: $BACKUP_DIR"

# 2. Copy new files
echo "[2/5] Copying new files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/app/email_notifier.py" "$VIGIL_DIR/app/"
cp "$SCRIPT_DIR/app/email_poller.py" "$VIGIL_DIR/app/"
cp "$SCRIPT_DIR/app/detection.py" "$VIGIL_DIR/app/"
cp "$SCRIPT_DIR/app/main.py" "$VIGIL_DIR/app/"
cp "$SCRIPT_DIR/docker-compose.yml" "$VIGIL_DIR/"
echo "  Files copied successfully."

# 3. Verify files exist
echo "[3/5] Verifying files..."
for f in "$VIGIL_DIR/app/email_notifier.py" "$VIGIL_DIR/app/email_poller.py" \
         "$VIGIL_DIR/app/detection.py" "$VIGIL_DIR/app/main.py"; do
  if [ -f "$f" ]; then
    echo "  ✅ $(basename $f)"
  else
    echo "  ❌ $(basename $f) not found!"
    exit 1
  fi
done

# 4. Restart Vigil API container
echo "[4/5] Restarting Vigil API container..."
docker compose -f "$VIGIL_DIR/docker-compose.yml" down 2>/dev/null || true
docker compose -f "$VIGIL_DIR/docker-compose.yml" up -d vigil-api
echo "  Container restarted."

# 5. Verify deployment
echo "[5/5] Verifying deployment..."
sleep 3

# Check email status endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/email/status 2>/dev/null || echo "000")
if [ "$STATUS" = "200" ]; then
  echo "  ✅ Email endpoints active (HTTP $STATUS)"
  curl -s http://localhost:8000/email/status | python3 -m json.tool 2>/dev/null || true
else
  echo "  ⚠️  Email endpoints returned HTTP $STATUS (may need more time to start)"
fi

# Start email poller container
echo ""
echo "=== Starting email poller container ==="
docker compose -f "$VIGIL_DIR/docker-compose.yml" up -d vigil-email-poller
echo "Email poller started."

echo ""
echo "=== Deploy Complete ==="
echo ""
echo "Next steps:"
echo "  1. Send a test email: curl http://localhost:8000/email/test"
echo "  2. Check poller logs: docker compose logs -f vigil-email-poller"
echo "  3. Monitor critical/high alerts — emails will send automatically"
echo ""
echo "Backup location: $BACKUP_DIR"
