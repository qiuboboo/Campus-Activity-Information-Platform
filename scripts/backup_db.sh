#!/usr/bin/env bash
# ============================================================
# backup_db.sh — Backup the Campus Platform PostgreSQL database
# ============================================================
# Usage:  ./scripts/backup_db.sh [output_dir]
# Default output dir: /home/workspace/backups/campus-platform
#
# Requirements: docker-compose must be available in PATH, and
# the postgres container must be running.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

# Output directory
OUTPUT_DIR="${1:-/home/workspace/backups/campus-platform}"
COMMIT="$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$OUTPUT_DIR/campus_${TIMESTAMP}_${COMMIT}.sql"

mkdir -p "$OUTPUT_DIR"

if ! docker-compose -f "$BACKEND_DIR/docker-compose.yml" ps --services 2>/dev/null | grep -q postgres; then
    echo "ERROR: postgres container is not running. Start it with:"
    echo "  cd $BACKEND_DIR && docker-compose up -d postgres"
    exit 1
fi

echo "Backing up PostgreSQL database..."
echo "  Output: $BACKUP_FILE"

docker-compose -f "$BACKEND_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U campus campus_activity > "$BACKUP_FILE"

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup complete: $FILE_SIZE"

# Keep only the last 14 backups
find "$OUTPUT_DIR" -name 'campus_*.sql' -type f | sort | head -n -14 | xargs -r rm

echo "Pruned old backups (kept last 14)"
