# OpsIQ Credential Rotation Guide

## Immediate Action Required

The following credentials are **exposed in `.env`** and must be rotated:

| Service | Key Location | How to Rotate |
|---------|-------------|---------------|
| **Google API** | `GOOGLE_API_KEY` | https://console.cloud.google.com/apis/credentials → Regenerate key |
| **Shopify** | `SHOPIFY_API_KEY`, `SHOPIFY_PASSWORD`, `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_CLIENT_SECRET` | Shopify Admin → Settings → Apps → Develop apps → Regenerate |
| **Resend** | `RESEND_API_KEY` | https://resend.com/api-keys → Revoke old → Create new |
| **OpsIQ API** | `API_KEY` | Generate: `openssl rand -hex 32` |

## Rotation Steps

### 1. Google API Key
```
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find the key named "OpsIQ" or similar
3. Click "Edit" → "Regenerate key"
4. Copy the new key
5. Update .env and .env.docker
6. Update any running containers: docker compose restart api
```

### 2. Shopify Credentials
```
1. Go to: https://admin.shopify.com/store/ecom-ops-automation-system/settings/apps
2. Go to "Develop apps" → Select your app
3. Under "API credentials":
   - Regenerate API key
   - Regenerate API secret key
4. Under "Admin API access token":
   - Revoke old token
   - Generate new token
5. Update .env with all new values
6. docker compose restart api
```

### 3. Resend API Key
```
1. Go to: https://resend.com/api-keys
2. Click "..." on the existing key → Revoke
3. Click "Create API Key" → Name: "OpsIQ Production"
4. Copy the new key
5. Update .env
6. docker compose restart api
```

### 4. OpsIQ API Key
```bash
# Generate a new secure key
openssl rand -hex 32

# Update .env
API_KEY=<new-generated-key>

# Update .env.docker
API_KEY=<new-generated-key>

# Restart
docker compose restart api
```

### 5. Grafana Admin Password
```bash
# Generate a new password
openssl rand -base64 24

# Update docker-compose.yml or .env.docker
GRAFANA_ADMIN_PASSWORD=<new-password>

# Restart
docker compose restart grafana
```

### 6. PostgreSQL Password
```bash
# Generate a new password
openssl rand -base64 32

# Update .env.docker
POSTGRES_PASSWORD=<new-password>
DATABASE_URL=postgresql+asyncpg://postgres:<new-password>@postgres:5432/ecommerce_ops

# Update all services that connect to the database
# Recreate the postgres container
docker compose down postgres
docker compose up -d postgres
```

## After Rotation

1. **Verify services are healthy:**
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

2. **Update CI/CD secrets** (GitHub Actions):
   - Go to: https://github.com/Ismail-2001/ecom-ops-automation-system/settings/secrets/actions
   - Update `DEEPSEEK_API_KEY`, `SHOPIFY_*` if used in CI

3. **Update `.gitignore`** — ensure `.env` is always ignored (already configured)

4. **Check for leaked keys in git history:**
   ```bash
   # If you committed .env before, the keys are in git history
   # Use BFG Repo-Cleaner to remove them:
   bfg --delete-files .env
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   ```

## Production Secrets Management

For production, use one of:
- **Docker Secrets**: `docker compose --secret` with `secrets/` files
- **AWS Secrets Manager**: Store in AWS, fetch at runtime
- **HashiCorp Vault**: Enterprise-grade secrets management
- **GitHub Actions Secrets**: For CI/CD pipelines
- **Kubernetes Secrets**: If running on K8s

Never put real secrets in:
- `.env` (committed to git)
- `.env.docker` (committed to git)
- Source code files
- Docker Compose files
- CI/CD pipeline files
