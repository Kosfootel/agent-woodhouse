#!/bin/bash

# Deploy updated dashboard to GX-10

echo "Deploying updated dashboard to GX-10..."

# Copy essential dashboard files (excluding node_modules)
rsync -avz --exclude node_modules --exclude .git --exclude .next \
  -e "ssh -i ~/.ssh/id_ed25519_woodhouse" \
  /Users/FOS_Erik/.openclaw/workspace/projects/vigil-home/dashboard/ \
  gx-10:/home/erik-ross/projects/vigil-home/dashboard/

# Copy deployment files
rsync -avz -e "ssh -i ~/.ssh/id_ed25519_woodhouse" \
  /Users/FOS_Erik/.openclaw/workspace/projects/vigil-home/deployment/gx10/ \
  gx-10:/home/erik-ross/projects/vigil-home/deployment/gx10/

echo "Files copied to GX-10. Building and deploying containers..."

# SSH to GX-10 and build/deploy
ssh -i ~/.ssh/id_ed25519_woodhouse gx-10 << 'EOF'
cd /home/erik-ross/projects/vigil-home

# Build the dashboard container
cd dashboard
docker build -t vigil-dashboard .

# Stop and remove existing dashboard container if running
docker stop vigil-dashboard 2>/dev/null || true
docker rm vigil-dashboard 2>/dev/null || true

# Run the new dashboard container
docker run -d \
  --name vigil-dashboard \
  --restart unless-stopped \
  -p 3000:3000 \
  -e VIGIL_API_URL=http://192.168.50.30:8000 \
  vigil-dashboard

echo "Dashboard deployed successfully!"
EOF