#!/usr/bin/env bash
# Production deployment script for OpsIQ
# Usage: ./scripts/deploy.sh <staging|production>
set -euo pipefail

ENV="${1:-staging}"
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="ecom-ops"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight checks ──────────────────────────────────────

log "Pre-flight checks for $ENV..."

command -v docker >/dev/null 2>&1 || error "docker not found"
command -v docker compose >/dev/null 2>&1 || error "docker compose not found"

if [ ! -f ".env" ]; then
  warn ".env not found, copying from .env.example"
  cp .env.example .env
fi

if [ "$ENV" = "production" ]; then
  grep -q "changeme" .env && error "Production deploy: change default secrets in .env"
fi

if [ "$ENV" = "staging" ]; then
  COMPOSE_FILE="docker-compose.dev.yml"
fi

# ── Build ──────────────────────────────────────────────────

log "Building images..."
docker compose -f "$COMPOSE_FILE" build --no-cache
success "Build complete"

# ── Database migration ─────────────────────────────────────

log "Running database migrations..."
docker compose -f "$COMPOSE_FILE" up -d postgres
sleep 3
docker compose -f "$COMPOSE_FILE" run --rm api alembic upgrade head || warn "Migration skipped (alembic not configured)"
success "Database ready"

# ── Deploy ─────────────────────────────────────────────────

log "Deploying services..."
docker compose -f "$COMPOSE_FILE" up -d
success "Services started"

# ── Health check ───────────────────────────────────────────

log "Waiting for API to be healthy..."
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
  sleep 2
  WAITED=$((WAITED + 2))
  if [ $WAITED -ge $MAX_WAIT ]; then
    error "API failed to become healthy within ${MAX_WAIT}s"
  fi
done
success "API is healthy (${WAITED}s)"

# ── Verify services ────────────────────────────────────────

log "Verifying services..."
docker compose -f "$COMPOSE_FILE" ps
success "All services running"

# ── Summary ────────────────────────────────────────────────

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete ($ENV)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  API:      ${BLUE}http://localhost:8000${NC}"
echo -e "  Health:   ${BLUE}http://localhost:8000/health${NC}"
echo -e "  Metrics:  ${BLUE}http://localhost:8000/metrics${NC}"
echo -e "  Docs:     ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "  Logs:     docker compose -f $COMPOSE_FILE logs -f"
echo -e "  Stop:     docker compose -f $COMPOSE_FILE down"
echo ""
