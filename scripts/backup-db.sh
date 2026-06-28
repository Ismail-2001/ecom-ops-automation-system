#!/usr/bin/env bash
# Automated PostgreSQL backup for OpsIQ
# Usage: ./scripts/backup-db.sh [output_dir]
set -euo pipefail

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BACKUP_FILE="${OUTPUT_DIR}/ecom_ops_${TIMESTAMP}.sql.gz"
CONTAINER_NAME="ecom-ops-postgres-1"
DB_NAME="${POSTGRES_DB:-ecommerce_ops}"
DB_USER="${POSTGRES_USER:-postgres}"

mkdir -p "$OUTPUT_DIR"

echo "[1/3] Dumping database..."
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[2/3] Verifying backup..."
BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
if [ "$BACKUP_SIZE" -lt 100 ]; then
  echo "[ERROR] Backup too small ($BACKUP_SIZE bytes), likely empty"
  rm -f "$BACKUP_FILE"
  exit 1
fi
echo "  Size: $(numfmt --to=iec "$BACKUP_FILE" 2>/dev/null || echo "${BACKUP_SIZE} bytes")"

echo "[3/3] Cleaning old backups (keep 7 days)..."
find "$OUTPUT_DIR" -name "ecom_ops_*.sql.gz" -mtime +7 -delete 2>/dev/null || true

echo ""
echo "[OK] Backup complete: $BACKUP_FILE"
ls -lh "$OUTPUT_DIR"/ecom_ops_*.sql.gz 2>/dev/null | tail -5
