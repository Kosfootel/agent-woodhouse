#!/bin/bash
# Vigil Dashboard Build & Deploy Script
# Source:  agent-woodhouse (Kosfootel/agent-woodhouse)
# Target:  agent-shared/vigil/ (Kosfootel/agent-shared)

set -e

VIGIL_SOURCE="$HOME/.openclaw/workspace/projects/vigil-home/dashboard"
HUB_TARGET="$HOME/.openclaw/workspace/projects/agent-shared/vigil"

echo "=== Building Vigil Dashboard ==="
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
echo "=== Target contents ==="
ls -la "$HUB_TARGET/"
echo ""
echo "=== hub/vigil/.next/ ==="
ls -la "$HUB_TARGET/.next/" 2>/dev/null
