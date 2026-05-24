#!/usr/bin/env bash
# Quick memory check and cleanup for dev environment
# Usage: ./scripts/memcheck.sh

set -e

THRESHOLD_MB=2800  # warn if usage exceeds this

echo "=== Memory Status ==="
free -h
echo ""

USED_MB=$(free -m | awk '/Mem:/ {print $3}')
AVAIL_MB=$(free -m | awk '/Mem:/ {print $7}')

echo "Used: ${USED_MB}MB / Available: ${AVAIL_MB}MB"

# Docker container summary
echo ""
echo "=== Docker Containers ==="
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null

# Top memory processes (non-container)
echo ""
echo "=== Top Processes ==="
ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "%-6s %5s %s\n", $2, $4"%", $11}'

echo ""

if [ "$USED_MB" -gt "$THRESHOLD_MB" ]; then
  echo "⚠️  Memory usage high (${USED_MB}MB > ${THRESHOLD_MB}MB)"
  echo "Quick fixes:"
  echo "  docker stop campus-activity-beat       # stop celery beat"
  echo "  docker stop campus-activity-searxng     # stop search engine"
  echo "  docker stop campus-activity-copilot-proxy # stop AI proxy"
  echo "  sync && echo 3 | sudo tee /proc/sys/vm/drop_caches  # drop page cache"
else
  echo "✅ Memory OK"
fi
