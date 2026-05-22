#!/usr/bin/env bash
# ============================================================
# restore_db.sh — Restore the Campus Platform PostgreSQL database
# ============================================================
# Usage:
#   ./scripts/restore_db.sh <backup_file>
#
# WARNING: This will OVERWRITE the current database. Use with
# caution on production. Always confirm the target before restore.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Example:"
    echo "  $0 /home/workspace/backups/campus-platform/campus_20260507_120000_abc1234.sql"
    echo ""
    echo "WARNING: This will OVERWRITE the current database!"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=== WARNING ==="
echo "You are about to RESTORE the database from:"
echo "  $BACKUP_FILE"
echo ""
echo "This will OVERWRITE all current data in PostgreSQL."
echo ""

read -r -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

if ! docker-compose -f "$BACKEND_DIR/docker-compose.yml" ps --services 2>/dev/null | grep -q postgres; then
    echo "ERROR: postgres container is not running."
    exit 1
fi

echo "Restoring database from $BACKUP_FILE ..."

# Drop and recreate the database, then restore
docker-compose -f "$BACKEND_DIR/docker-compose.yml" exec -T postgres \
    psql -U campus -d postgres -c "DROP DATABASE IF EXISTS campus_activity;"
docker-compose -f "$BACKEND_DIR/docker-compose.yml" exec -T postgres \
    psql -U campus -d postgres -c "CREATE DATABASE campus_activity OWNER campus;"
docker-compose -f "$BACKEND_DIR/docker-compose.yml" exec -T postgres \
    psql -U campus -d campus_activity < "$BACKUP_FILE"

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Restore complete! ($FILE_SIZE restored)"
echo ""
echo "Next steps:"
echo "  1. Restart the API and Worker containers:"
echo "     cd $BACKEND_DIR && docker-compose restart api worker"
echo "  2. Verify health: curl http://127.0.0.1:5000/api/health"
echo "  3. Run smoke test: ./scripts/smoke_backend.sh"
