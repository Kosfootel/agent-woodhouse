#!/usr/bin/env bash
# a2a-reliable-send.sh — bulletproof A2A send with retry
# Usage: ./a2a-reliable-send.sh <peer-url> <token> <message>
# Retries up to MAX_ATTEMPTS times with exponential backoff.
# Exits 0 on success, 1 on all attempts exhausted.
#
# P2 fix (2026-04-02): writes delivery confirmation to a result file
# so callers are not dependent on stdout capture within a racing exec shell.
# Result file: /tmp/a2a-send-result-<timestamp>.txt
# Contains either "DELIVERED:attempt=N" or "FAILED"

set -euo pipefail

PEER_URL="${1:?Usage: $0 <peer-url> <token> <message>}"
TOKEN="${2:?missing token}"
MESSAGE="${3:?missing message}"

A2A_SEND="$HOME/.openclaw/extensions/a2a-gateway/skill/scripts/a2a-send.mjs"
RESULT_FILE="/tmp/a2a-send-result-$$.txt"

# Clean up result file on exit (trap before any early exits)
trap 'rm -f "$RESULT_FILE"' EXIT

MAX_ATTEMPTS=5
BACKOFF=5  # seconds between first retry

# Strip /a2a/jsonrpc suffix for agent-card check
BASE_URL="$PEER_URL"

attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
  echo "[a2a-reliable-send] Attempt $attempt/$MAX_ATTEMPTS → $PEER_URL"

  # Quick connectivity pre-check
  if ! curl -sf --max-time 5 "${BASE_URL}/.well-known/agent-card.json" > /dev/null 2>&1; then
    echo "[a2a-reliable-send] Peer not reachable, waiting ${BACKOFF}s..."
    sleep $BACKOFF
    BACKOFF=$(( BACKOFF * 2 ))
    attempt=$(( attempt + 1 ))
    continue
  fi

  # Attempt send — extended timeout for slow peers (Ray)
  if node "$A2A_SEND" \
      --peer-url "$PEER_URL" \
      --token "$TOKEN" \
      --non-blocking --wait --timeout-ms 300000 \
      --message "$MESSAGE"; then
    echo "[a2a-reliable-send] ✓ Delivered on attempt $attempt"
    echo "DELIVERED:attempt=$attempt" > "$RESULT_FILE"
    # Print result file path so callers can poll it
    echo "[a2a-reliable-send] Result written to: $RESULT_FILE"
    exit 0
  fi

  echo "[a2a-reliable-send] Send failed, waiting ${BACKOFF}s before retry..."
  sleep $BACKOFF
  BACKOFF=$(( BACKOFF * 2 ))
  attempt=$(( attempt + 1 ))
done

echo "[a2a-reliable-send] ✗ All $MAX_ATTEMPTS attempts failed for $PEER_URL"
echo "FAILED" > "$RESULT_FILE"
exit 1
