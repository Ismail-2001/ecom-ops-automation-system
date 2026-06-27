# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within OpsIQ, please send an email to security@opsiq.ai. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to include

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix & Disclosure**: Within 30 days

## Security Measures

### Authentication

- JWT tokens with configurable expiration
- API key authentication
- Rate limiting on all endpoints
- Brute force protection

### Authorization

- Role-Based Access Control (RBAC)
- 30+ granular permissions
- 5 predefined roles (super_admin, admin, operator, viewer, api_only)
- Resource-level access control

### Data Protection

- Passwords hashed with bcrypt
- API keys encrypted at rest
- Sensitive data masked in logs
- HTTPS enforced in production

### Input Validation

- Request body validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (security headers)
- Input sanitization middleware

### Monitoring

- Audit logging for all security events
- Failed login attempt tracking
- Rate limit violation monitoring
- Anomaly detection

### Infrastructure

- Docker container isolation
- Network segmentation
- Database access restricted
- Redis access restricted
- Regular security updates

## Best Practices

### For Developers

1. Never commit secrets to version control
2. Use environment variables for configuration
3. Validate all user input
4. Use parameterized queries
5. Implement proper error handling
6. Follow the principle of least privilege
7. Keep dependencies updated
8. Run security scans in CI/CD

### For Deployment

1. Use HTTPS in production
2. Enable firewall
3. Restrict database access
4. Use strong passwords
5. Enable audit logging
6. Monitor for suspicious activity
7. Regular backups
8. Keep systems updated

### For API Usage

1. Use API keys for programmatic access
2. Rotate API keys regularly
3. Use HTTPS only
4. Implement rate limiting
5. Validate webhook signatures
6. Don't expose sensitive data

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2). Users are encouraged to always use the latest version.

### Update Process

1. Security vulnerability reported
2. Fix developed and tested
3. Security patch released
4. Users notified via GitHub Security Advisories
5. CVE assigned (if applicable)

## Compliance

### GDPR

- Data minimization
- Right to erasure
- Data portability
- Consent management
- Privacy by design

### SOC 2

- Access controls
- Audit logging
- Encryption at rest and in transit
- Incident response procedures
- Regular security assessments

### PCI DSS

- No credit card data stored
- Secure transmission
- Access controls
- Regular testing
- Security policies

## Contact

For security-related inquiries:

- **Email**: security@opsiq.ai
- **PGP Key**: Available on request
- **Bug Bounty**: Coming soon

## Acknowledgments

We thank the security researchers who help us improve the security of OpsIQ. Responsible disclosure is appreciated.

## License

This security policy is part of the OpsIQ project and is licensed under the MIT License.
