#!/usr/bin/env bash
# ── OpsIQ Production Deploy ────────────────────────────────
# One-command production deployment
# Usage: ./scripts/deploy.sh [action]
#   action: up (default), down, restart, logs, status, backup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.yml"
BACKUP_FILE="docker-compose.backup.yml"
ACTION="${1:-up}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
fail()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Pre-flight Checks ──────────────────────────────────────
preflight() {
    log "Running pre-flight checks..."

    command -v docker >/dev/null 2>&1 || fail "Docker not installed"
    docker info >/dev/null 2>&1 || fail "Docker daemon not running"

    # Check for required files
    for f in "$PROJECT_DIR/docker-compose.yml" "$PROJECT_DIR/.env.docker"; do
        [[ -f "$f" ]] || fail "Missing required file: $f"
    done

    # Check for TLS certs (warn if missing)
    if [[ ! -f "$PROJECT_DIR/nginx/certs/server.crt" ]]; then
        warn "TLS certs not found — HTTPS will be disabled"
        warn "Run: bash scripts/generate-tls-certs.sh"
    fi

    # Ensure backup compose exists
    if [[ ! -f "$PROJECT_DIR/$BACKUP_FILE" ]]; then
        warn "Backup compose not found — skipping backup services"
        BACKUP_FILE=""
    fi

    ok "Pre-flight checks passed"
}

# ── Deploy ──────────────────────────────────────────────────
deploy_up() {
    preflight

    log "Starting OpsIQ production stack..."

    COMPOSE_CMD="docker compose -f $COMPOSE_FILE"
    [[ -n "${BACKUP_FILE:-}" && -f "$PROJECT_DIR/$BACKUP_FILE" ]] && \
        COMPOSE_CMD="$COMPOSE_CMD -f $BACKUP_FILE"

    cd "$PROJECT_DIR"

    # Pull latest images
    log "Pulling latest images..."
    $COMPOSE_CMD pull --quiet 2>/dev/null || true

    # Build API image
    log "Building API image..."
    $COMPOSE_CMD build api --quiet

    # Stop existing services gracefully
    log "Stopping existing services..."
    $COMPOSE_CMD down --timeout 30 2>/dev/null || true

    # Start services
    log "Starting services..."
    $COMPOSE_CMD up -d --remove-orphans --force-recreate

    # Wait for health
    log "Waiting for services to become healthy..."
    local max_wait=120
    local elapsed=0
    while [[ $elapsed -lt $max_wait ]]; do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            ok "API is healthy!"
            break
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        log "  Waiting... (${elapsed}s/${max_wait}s)"
    done

    if [[ $elapsed -ge $max_wait ]]; then
        warn "API health check timed out after ${max_wait}s"
        warn "Check logs: docker compose logs api"
    fi

    # Show status
    deploy_status
}

# ── Status ──────────────────────────────────────────────────
deploy_status() {
    cd "$PROJECT_DIR"
    log "Service status:"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    log "Health check:"
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        ok "API: healthy"
    else
        warn "API: unhealthy or unreachable"
    fi

    if curl -sf http://localhost:9093/-/healthy >/dev/null 2>&1; then
        ok "Prometheus: healthy"
    else
        warn "Prometheus: unhealthy or unreachable"
    fi
}

# ── Logs ────────────────────────────────────────────────────
deploy_logs() {
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100 "${@:2}"
}

# ── Backup ──────────────────────────────────────────────────
deploy_backup() {
    cd "$PROJECT_DIR"
    local backup_dir="$PROJECT_DIR/backups/$TIMESTAMP"
    mkdir -p "$backup_dir"

    log "Creating database backup..."
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
        pg_dump -U postgres ecommerce_ops | gzip > "$backup_dir/postgres.sql.gz"

    log "Creating Redis backup..."
    docker compose -f "$COMPOSE_FILE" exec -T redis \
        redis-cli BGSAVE >/dev/null 2>&1 || true
    sleep 2
    docker compose -f "$COMPOSE_FILE" exec -T redis \
        redis-cli LASTSAVE > "$backup_dir/redis_lastsave.txt" 2>/dev/null || true

    log "Backing up configuration..."
    cp "$PROJECT_DIR/.env.docker" "$backup_dir/"
    cp "$PROJECT_DIR/docker-compose.yml" "$backup_dir/"
    cp -r "$PROJECT_DIR/monitoring" "$backup_dir/" 2>/dev/null || true

    ok "Backup created: $backup_dir"
    ls -la "$backup_dir"
}

# ── Main ────────────────────────────────────────────────────
case "$ACTION" in
    up|deploy)  deploy_up ;;
    down|stop)
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" down --timeout 30
        ok "Stack stopped"
        ;;
    restart)
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" restart
        ok "Stack restarted"
        ;;
    status)     deploy_status ;;
    logs)       deploy_logs "$@" ;;
    backup)     deploy_backup ;;
    *)
        echo "Usage: $0 {up|down|restart|status|logs|backup}"
        exit 1
        ;;
esac
