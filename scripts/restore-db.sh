#!/bin/bash
# ── OpsIQ — Database Restore Script ────────────────────────
# Usage: ./scripts/restore-db.sh <backup_file>

set -euo pipefail

BACKUP_FILE="${1:-}"
CONTAINER_NAME="opsiq-postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    docker exec $CONTAINER_NAME ls -la /backups/*.dump.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  This will OVERWRITE the current database!"
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Stopping API service..."
docker compose stop api

echo "Dropping and recreating database..."
docker exec $CONTAINER_NAME psql -U postgres -c "DROP DATABASE IF EXISTS ecommerce_ops;"
docker exec $CONTAINER_NAME psql -U postgres -c "CREATE DATABASE ecommerce_ops;"

echo "Restoring from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME pg_restore -U postgres -d ecommerce_ops --no-owner --no-acl
else
    docker exec -i $CONTAINER_NAME pg_restore -U postgres -d ecommerce_ops --no-owner --no-acl < "$BACKUP_FILE"
fi

echo "Running migrations..."
docker compose run --rm api alembic upgrade head

echo "Starting API service..."
docker compose start api

echo "✅ Restore complete!"
