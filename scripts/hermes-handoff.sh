#!/bin/bash
# Vigil Device Identification - Hermes Handoff Script
# Run this script to submit the spec to Hermes for implementation

set -e

echo "=== Vigil Device Identification - Hermes Handoff ==="
echo ""

# Ensure we're on GX-10
if [[ "$(hostname)" != "gx-10" ]]; then
    echo "ERROR: This script must be run on GX-10"
    echo "Please SSH to GX-10 and run from there"
    exit 1
fi

VIGIL_DIR="$HOME/projects/vigil-home"
INBOX_DIR="$HOME/hermes/inbox"

echo "Source: $VIGIL_DIR"
echo "Destination: $INBOX_DIR"
echo ""

# Ensure inbox directory exists
mkdir -p "$INBOX_DIR"

# Create handoff package
PACKAGE_NAME="vigil-device-identification-$(date +%Y%m%d-%H%M%S)"
PACKAGE_DIR="$INBOX_DIR/$PACKAGE_NAME"

echo "Creating handoff package: $PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"

# Copy spec
cp "$VIGIL_DIR/specs/device-identification-spec.md" "$PACKAGE_DIR/SPEC.md"

# Copy discovery module
cp "$VIGIL_DIR/poc-backend/app/device_discovery.py" "$PACKAGE_DIR/"

# Create a summary file
cat > "$PACKAGE_DIR/HANDOFF.md" << 'EOF'
# Vigil Device Identification - Hermes Handoff

**Submitted:** $(date)
**From:** Woodhouse
**Priority:** High

## Summary

Implement enhanced device identification for Vigil using active discovery methods.

## Key Deliverables

1. **Database Schema** - Add tables for discovery sources and IP history
2. **API Endpoints** - Discovery, nickname, type management endpoints
3. **Integration** - Wire up device_discovery.py to FastAPI app
4. **Classification** - Enhance classifier to use discovery data

## Files Provided

- `device_discovery.py` - Complete discovery service implementation
- `SPEC.md` - Full specification with database schema and API definitions
- `HANDOFF.md` - This file

## Starting Points

- Database: `~/projects/vigil-home/vigil.db`
- Backend: `~/projects/vigil-home/poc-backend/`
- Models: `~/projects/vigil-home/poc-backend/app/models.py`
- Main: `~/projects/vigil-home/poc-backend/app/main.py`

## On Blocked

Return questions in `~/projects/vigil-home/hermes/on_blocked.md`
Woodhouse will respond with clarification.

## Expected Output

- Database migration applied
- New API endpoints working
- Discovery service integrated
- Device classification improved

EOF

echo "✅ Handoff package created: $PACKAGE_DIR"
echo ""
echo "Contents:"
ls -la "$PACKAGE_DIR/"
echo ""
echo "Ready for Hermes pickup"
