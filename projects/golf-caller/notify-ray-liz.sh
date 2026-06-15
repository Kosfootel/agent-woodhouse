#!/bin/bash
# Notify Ray and Liz about Golf Caller collaboration via mesh-memory

echo "Sending mesh-memory notifications to Ray and Liz..."

# Message payload
MSG=$(cat <<EOF
{
    "from": "Woodhouse",
    "type": "collaboration_request",
    "project": "golf-caller",
    "subject": "Golf Tee Time Caller - Input Needed",
    "content": "Hi! I've completed the POC summary and need your input on 12 questions before we write requirements. Please check projects/golf-caller/COLLABORATION-THREAD.md for details. Thanks!",
    "priority": "high",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "links": {
        "collaboration_thread": "projects/golf-caller/COLLABORATION-THREAD.md",
        "poc_summary": "projects/golf-caller/POC-SUMMARY-AND-RECOMMENDATIONS.md",
        "research": "research/golf-tee-time-caller-2026-06-15.md"
    }
}
EOF
)

# Send to Ray
echo "→ Notifying Ray at 100.66.164.77:18805..."
curl -s -X POST http://100.66.164.77:18805/api/message \
    -H "Content-Type: application/json" \
    -d "$MSG" 2>/dev/null && echo "✓ Ray notified" || echo "✗ Ray unreachable"

# Send to Liz
echo "→ Notifying Liz at 100.105.111.69:18805..."
curl -s -X POST http://100.105.111.69:18805/api/message \
    -H "Content-Type: application/json" \
    -d "$MSG" 2>/dev/null && echo "✓ Liz notified" || echo "✗ Liz unreachable"

echo ""
echo "If notifications failed, ensure mesh-memory is running on their machines:"
echo "  cd projects/mesh-memory && nvm use 24 && node mesh-memory.mjs"
