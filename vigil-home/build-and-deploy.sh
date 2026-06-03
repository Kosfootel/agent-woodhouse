#!/bin/bash
# Vigil Dashboard Build & Deploy Script
# Supports multi-target deployment:
#   - GX-10 (direct API access):  VIGIL_API_BASE=http://192.168.50.30:8000
#   - bettermachine-host (proxied): VIGIL_BASE_PATH=/vigil VIGIL_API_BASE=/api
#
# Usage:
#   ./build-and-deploy.sh              # Default: GX-10 target
#   VIGIL_BASE_PATH=/vigil VIGIL_API_BASE=/api ./build-and-deploy.sh  # bettermachine-host

set -e

VIGIL_SOURCE="$HOME/.openclaw/workspace/projects/vigil-home/dashboard"
HUB_TARGET="$HOME/.openclaw/workspace/projects/agent-shared/vigil"

# Default to GX-10 direct access if no env vars set
export VIGIL_API_BASE="${VIGIL_API_BASE:-http://192.168.50.30:8000}"
export VIGIL_BASE_PATH="${VIGIL_BASE_PATH:-}"

echo "=== Building Vigil Dashboard ==="
echo "  API_BASE:  $VIGIL_API_BASE"
echo "  BASE_PATH: $VIGIL_BASE_PATH"
cd "$VIGIL_SOURCE"
npm run build

echo ""
echo "=== Copying to hub/agent-shared/vigil/ ==="
rm -rf "$HUB_TARGET"
mkdir -p "$HUB_TARGET"

# 1. Copy standalone deployment (server.js, package.json, .next/server configs)
cp -r .next/standalone/* "$HUB_TARGET/"

# 2. Copy .next/standalone/.next (BUILD_ID, runtime config files)
cp -r .next/standalone/.next "$HUB_TARGET/"

# 3. Copy static chunks (not in standalone output)
mkdir -p "$HUB_TARGET/.next/static"
cp -r .next/static/* "$HUB_TARGET/.next/static/"

# 4. Copy public assets
cp -r public "$HUB_TARGET/" 2>/dev/null || true

# 5. Remove node_modules (installed on target via npm install)
rm -rf "$HUB_TARGET/node_modules"

# 6. Write .gitignore
cat > "$HUB_TARGET/.gitignore" << 'GITEOF'
# Override root .gitignore for vigil deploy artifacts
!.next
!.next/
!.next/**
!.next/server/**
node_modules/
.next/cache/
GITEOF

echo ""
echo "=== Done. Next steps: ==="
echo "  cd $HUB_TARGET"
echo "  npm install          # install Next.js runtime deps"
echo "  git add -A"
echo "  git commit -m 'Update vigil dashboard'"
echo "  git push"
echo ""
echo "  For bettermachine-host:"
echo "    rsync -avz --delete $HUB_TARGET/ erik-ross@bettermachine-host:/opt/vigil-dashboard/.next/standalone/"
echo "    rsync -avz --delete $VIGIL_SOURCE/.next/static/ erik-ross@bettermachine-host:/opt/vigil-dashboard/.next/static/"
echo "    ssh erik-ross@bettermachine-host 'sudo systemctl restart vigil-dashboard.service'"
echo ""
echo "=== Target contents ==="
ls -la "$HUB_TARGET/"
echo ""
echo "=== hub/vigil/.next/ ==="
ls -la "$HUB_TARGET/.next/" 2>/dev/null
