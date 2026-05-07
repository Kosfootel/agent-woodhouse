#!/bin/bash
# Deploy Vigil to GX-10
# Run from Woodhouse or any mesh node with SSH access

set -e

GX10_HOST="192.168.50.30"
GX10_USER="erik-ross"
DEPLOY_PATH="/opt/vigil"

echo "=== Vigil GX-10 Deployment Script ==="
echo "Target: ${GX10_USER}@${GX10_HOST}:${DEPLOY_PATH}"
echo ""

# Check connectivity
echo "[1/6] Checking connectivity..."
if ! ping -c 1 -W 2 $GX10_HOST &> /dev/null; then
    echo "ERROR: Cannot reach GX-10 at ${GX10_HOST}"
    exit 1
fi
echo "✓ GX-10 reachable"

# Create remote directory
echo "[2/6] Creating deployment directory..."
ssh ${GX10_USER}@${GX10_HOST} "sudo mkdir -p ${DEPLOY_PATH} && sudo chown ${GX10_USER}: ${DEPLOY_PATH}"
echo "✓ Directory ready"

# Copy deployment files
echo "[3/6] Copying deployment files..."
scp docker-compose.gx10.yml ${GX10_USER}@${GX10_HOST}:${DEPLOY_PATH}/
scp init.sql ${GX10_USER}@${GX10_HOST}:${DEPLOY_PATH}/
scp .env.example ${GX10_USER}@${GX10_HOST}:${DEPLOY_PATH}/.env
scp vigil-api.service ${GX10_USER}@${GX10_HOST}:/tmp/
echo "✓ Files copied"

# Build and start
echo "[4/6] Building and starting services..."
ssh ${GX10_USER}@${GX10_HOST} << EOF
cd ${DEPLOY_PATH}
docker-compose -f docker-compose.gx10.yml pull
docker-compose -f docker-compose.gx10.yml up -d
echo "✓ Services started"
EOF

# Install systemd service
echo "[5/6] Installing systemd service..."
ssh ${GX10_USER}@${GX10_HOST} << EOF
sudo mv /tmp/vigil-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vigil-api.service
echo "✓ Service installed"
EOF

# Verify
echo "[6/6] Verifying deployment..."
sleep 5
if ssh ${GX10_USER}@${GX10_HOST} "curl -sf http://localhost:8000/health" > /dev/null 2>&1; then
    echo "✓ Vigil API responding on port 8000"
else
    echo "⚠ API not responding yet (may need more time)"
fi

echo ""
echo "=== Deployment Complete ==="
echo "API URL: http://${GX10_HOST}:8000"
echo "Docs: http://${GX10_HOST}:8000/docs"
echo ""
echo "To check status:"
echo "  ssh ${GX10_USER}@${GX10_HOST} 'docker-compose -f ${DEPLOY_PATH}/docker-compose.gx10.yml ps'"
