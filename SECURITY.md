# Security Policy

## Supported Versions

| Version | Supported |
|:---|---:|
| 0.x (latest) | ✅ Active development — security fixes prioritized |

## Reporting a Vulnerability

OpsIQ handles ecommerce operations data including customer information, order details, and store credentials. We take security seriously.

### How to Report

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email: **admin@example.com**

Include:
- A clear description of the vulnerability
- Steps to reproduce (PoC preferred)
- Potential business impact (data exposure, credential leakage, etc.)
- Your contact information for follow-up

### What to Expect

1. **Acknowledgment** within 48 hours
2. **Investigation** and confirmation within 5 business days
3. **Fix timeline** communicated based on severity
4. **Credit** in release notes (if desired)

## Security Best Practices for Deployments

| Practice | Recommendation |
|:---|---:|
| API keys | Store in environment variables or a secrets manager (Doppler, 1Password). Never commit `.env` files. |
| Database | Use PostgreSQL with SSL in production. Avoid SQLite for production deployments. |
| Redis | Enable password authentication and TLS for Redis in production. |
| LLM keys | Use least-privilege API keys. Rotate keys every 90 days. |
| Network | Run OpsIQ behind a reverse proxy (nginx, Caddy) with HTTPS in production. |
| Dashboard | Add authentication (OAuth, SSO) before exposing the dashboard publicly. |
| Audit logs | Monitor audit trails regularly. Logs are immutable but should be backed up. |

## Known Security Features

- Prompt injection hardening on all user-facing LLM calls
- API keys encrypted via Pydantic `SecretStr` (masked in logs)
- Rate limiting per IP (configurable, Redis-backed)
- Circuit breakers prevent cascading failures
- SOC2-ready immutable audit trails
- Shadow mode for risk-free testing

## Responsible Disclosure

We believe in responsible disclosure. If you report a vulnerability:

- We will investigate and fix it promptly
- We will not take legal action against researchers acting in good faith
- We will publicly acknowledge your contribution (if desired)

Thank you for helping keep OpsIQ and the ecommerce ecosystem secure.
