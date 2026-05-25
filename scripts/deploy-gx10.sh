#!/bin/bash
# CI/CD Deployment Script for Vigil on GX-10
# Called by GitHub Actions workflow for automated deployments
#
# Usage: ./scripts/deploy-gx10.sh [IMAGE_TAG] [REGISTRY] [REPO_OWNER]
# Environment variables:
#   IMAGE_TAG - Docker image tag to deploy (defaults to 'latest')
#   REGISTRY - Container registry (defaults to 'ghcr.io')
#   REPO_OWNER - GitHub owner/org (defaults to 'Kosfootel')
#   GHCR_TOKEN - GitHub token for registry auth
#   GHCR_USER - GitHub username for registry auth

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIGIL_DIR="$HOME/projects/vigil-home"
TARGET_HOST="192.168.50.30"
COMPOSE_FILE="docker-compose.cicd.yml"

# Parameters (can be overridden by env vars)
IMAGE_TAG="${1:-${IMAGE_TAG:-latest}}"
REGISTRY="${2:-${REGISTRY:-ghcr.io}}"
REPO_OWNER="${3:-${REPO_OWNER:-Kosfootel}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running on GX-10 or via SSH
    local hostname=$(hostname)
    local current_ip=$(hostname -I | awk '{print $1}')
    
    if [[ "$hostname" != "gx10" && "$current_ip" != "$TARGET_HOST" && -z "${REMOTE_DEPLOY:-}" ]]; then
        log_warning "This script should run on GX-10 (192.168.50.30)"
        log_warning "Current: $hostname ($current_ip)"
        log_warning "For remote deployment, use GitHub Actions or set REMOTE_DEPLOY=1"
        
        if [[ "${REMOTE_DEPLOY:-}" != "1" ]]; then
            read -p "Continue anyway? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Check if compose file exists
    if [[ ! -f "$VIGIL_DIR/$COMPOSE_FILE" ]]; then
        log_warning "Compose file not found at $VIGIL_DIR/$COMPOSE_FILE"
        log_info "Attempting to sync from local repo..."
        sync_compose_file
    fi
    
    log_success "Prerequisites check passed"
}

# Sync compose file from repo to GX-10
sync_compose_file() {
    log_info "Syncing compose file to $VIGIL_DIR..."
    
    mkdir -p "$VIGIL_DIR"
    cp "$PROJECT_ROOT/$COMPOSE_FILE" "$VIGIL_DIR/"
    
    log_success "Compose file synced"
}

# Authenticate with GHCR
authenticate_ghcr() {
    if [[ -z "${GHCR_TOKEN:-}" ]]; then
        log_warning "GHCR_TOKEN not set. Skipping registry authentication."
        log_info "If images are public, this is fine."
        return 0
    fi
    
    log_info "Authenticating with GitHub Container Registry..."
    
    local username="${GHCR_USER:-$REPO_OWNER}"
    echo "$GHCR_TOKEN" | docker login "$REGISTRY" -u "$username" --password-stdin
    
    log_success "Authenticated with GHCR"
}

# Pull latest images
pull_images() {
    log_info "Pulling Docker images..."
    log_info "  Registry: $REGISTRY"
    log_info "  Owner: $REPO_OWNER"
    log_info "  Tag: $IMAGE_TAG"
    
    cd "$VIGIL_DIR"
    
    # Export variables for docker-compose
    export IMAGE_TAG
    export REGISTRY
    export REPO_OWNER
    
    # Pull images
    docker compose -f "$COMPOSE_FILE" pull dashboard backend
    
    log_success "Images pulled successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    cd "$VIGIL_DIR"
    
    # Export variables for docker-compose
    export IMAGE_TAG
    export REGISTRY
    export REPO_OWNER
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    docker compose -f "$COMPOSE_FILE" stop dashboard backend || true
    
    # Start services with new images
    log_info "Starting services with new images..."
    docker compose -f "$COMPOSE_FILE" up -d dashboard backend
    
    log_success "Services deployed"
}

# Health check
health_check() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local wait_seconds=2
    local backend_healthy=false
    local dashboard_healthy=false
    
    # Check backend
    log_info "Checking backend health..."
    for i in $(seq 1 $max_attempts); do
        if curl -fs "http://$TARGET_HOST:8000/health" > /dev/null 2>&1; then
            backend_healthy=true
            break
        fi
        if [[ $i -eq $max_attempts ]]; then
            log_error "Backend health check failed after $max_attempts attempts"
            return 1
        fi
        sleep $wait_seconds
    done
    
    if $backend_healthy; then
        log_success "Backend is healthy (http://$TARGET_HOST:8000)"
    fi
    
    # Check dashboard
    log_info "Checking dashboard health..."
    for i in $(seq 1 $max_attempts); do
        if curl -fs "http://$TARGET_HOST:8085" > /dev/null 2>&1; then
            dashboard_healthy=true
            break
        fi
        if [[ $i -eq $max_attempts ]]; then
            log_error "Dashboard health check failed after $max_attempts attempts"
            return 1
        fi
        sleep $wait_seconds
    done
    
    if $dashboard_healthy; then
        log_success "Dashboard is healthy (http://$TARGET_HOST:8085)"
    fi
    
    log_success "All health checks passed"
}

# Cleanup old images
cleanup_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove unused images older than 7 days (168 hours)
    docker image prune -a -f --filter "until=168h" || true
    
    log_success "Cleanup complete"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    cd "$VIGIL_DIR"
    
    # Restart with previous configuration
    docker compose -f "$COMPOSE_FILE" down dashboard backend || true
    docker compose -f "$COMPOSE_FILE" up -d dashboard backend || true
    
    log_info "Rollback complete"
}

# Show deployment status
show_status() {
    log_info "Current deployment status:"
    echo ""
    
    cd "$VIGIL_DIR"
    docker compose -f "$COMPOSE_FILE" ps dashboard backend
    
    echo ""
    log_info "Image versions:"
    docker compose -f "$COMPOSE_FILE" exec -T dashboard sh -c 'echo "Dashboard: $(cat /usr/share/nginx/html/version.txt 2>/dev/null || echo unknown)"' 2>/dev/null || true
    
    echo ""
    log_info "Endpoints:"
    echo "  Dashboard: http://$TARGET_HOST:8085"
    echo "  API:       http://$TARGET_HOST:8000"
    echo "  Health:    http://$TARGET_HOST:8000/health"
}

# Main deployment flow
main() {
    echo "============================================"
    echo "  Vigil CI/CD Deployment to GX-10"
    echo "============================================"
    echo "  Image Tag: $IMAGE_TAG"
    echo "  Registry:  $REGISTRY"
    echo "  Owner:     $REPO_OWNER"
    echo "  Target:    $TARGET_HOST"
    echo "============================================"
    echo ""
    
    # Handle rollback flag
    if [[ "${1:-}" == "--rollback" ]]; then
        rollback
        exit 0
    fi
    
    # Handle status flag
    if [[ "${1:-}" == "--status" ]]; then
        show_status
        exit 0
    fi
    
    # Run deployment
    check_prerequisites
    authenticate_ghcr
    pull_images
    deploy_services
    health_check
    cleanup_images
    
    echo ""
    echo "============================================"
    log_success "Deployment Complete!"
    echo "============================================"
    echo "  Dashboard: http://$TARGET_HOST:8085"
    echo "  API:       http://$TARGET_HOST:8000"
    echo "  Health:    http://$TARGET_HOST:8000/health"
    echo "============================================"
}

# Trap errors for rollback
trap 'log_error "Deployment failed!"; rollback; exit 1' ERR

# Run main
main "$@"
