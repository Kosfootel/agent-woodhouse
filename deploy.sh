#!/bin/bash
# Deploy Vigil from unified repo structure to GX-10 production

set -euo pipefail

TARGET_HOST="192.168.50.30"
TARGET_USER="erik-ross"
VIGIL_DIR="/home/erik-ross/vigil"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "============================================"
echo "Vigil Deployment to GX-10"
echo "Source: backend/ -> vigil/backend"
echo "============================================"
echo ""

# Check connectivity
echo "[1/5] Checking connectivity..."
ping -c 1 -W 2 "$TARGET_HOST" > /dev/null 2>&1 || { echo "ERROR: Cannot reach $TARGET_HOST"; exit 1; }
echo "✓ Host reachable"

# Create remote directory and sync backend
echo ""
echo "[2/5] Syncing backend to production..."

# Sync backend directory
timeout 30 rsync -avz --delete     --exclude='venv/'     --exclude='__pycache__/'     --exclude='*.pyc'     --exclude='*.db'     --exclude='*.log'     ./backend/     "$TARGET_USER@$TARGET_HOST:$VIGIL_DIR/backend/"

echo "✓ Backend synced"

# Restart services on GX-10
echo ""
echo "[3/5] Restarting services on GX-10..."
ssh $SSH_OPTS "$TARGET_USER@$TARGET_HOST" << 'EOSSH'
    cd /home/erik-ross/vigil
    
    echo "  Stopping containers..."
    docker stop vigil-backend vigil-dashboard vigil-caddy 2>/dev/null || true
    docker rm vigil-backend vigil-dashboard vigil-caddy 2>/dev/null || true
    
    echo "  Building and starting..."
    docker compose build backend
    docker compose up -d
    
    sleep 3
    echo "  Services restarted"
EOSSH

echo "✓ Services restarted"

# Health check
echo ""
echo "[4/5] Health checks..."
sleep 2
for endpoint in "http://$TARGET_HOST:8000/health" "http://$TARGET_HOST"; do
    if curl -fs "$endpoint" > /dev/null 2>&1; then
        echo "✓ $endpoint"
    else
        echo "⚠ $endpoint (may need more time)"
    fi
done

echo ""
echo "[5/5] Deployment complete!"
echo "  Dashboard: http://$TARGET_HOST"
echo "  API:       http://$TARGET_HOST:8000"
