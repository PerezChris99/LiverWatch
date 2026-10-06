# LiverWatch Security Architecture

## Security standard

LiverWatch uses OWASP ASVS as the practical verification baseline for web application controls and the OWASP API Security Top 10 as the API threat checklist.

## Control mapping

| Area | LiverWatch control |
|---|---|
| Authentication | Password hashing, login throttling, account lockout, short-lived JWT access tokens, issuer/audience validation, token-version revocation |
| Authorization | Server-side role checks and object-level ownership checks; default deny for cross-user health records |
| Input validation | WTForms validation, explicit API allow-lists, bounded lengths/ranges, finite numeric checks, timezone-aware timestamps |
| Resource consumption | Request-size limits, endpoint rate limits, bounded ingestion batches, pagination, bounded analytics datasets |
| CSRF | Global Flask-WTF CSRF protection for browser-cookie-backed state changes; bearer-token APIs are explicitly exempt |
| Session security | Secure production cookies, server-side authorization, token revocation on logout |
| Transport security | HTTPS/HSTS in production and configurable trusted reverse-proxy handling |
| Browser security | CSP, frame denial, MIME sniffing protection, referrer policy, permissions policy |
| Data protection | Encrypted protected PII, least privilege, consent and auditability |
| Database security | PostgreSQL production target, migrations as schema source of truth, foreign keys, integrity constraints, indexes, transaction rollback |
| Caching | Private health analytics use user-scoped cache keys; API responses are no-store |
| Logging | Request IDs, audit events, sanitized errors, security-relevant access logging |
| Supply chain | Dependency upgrade monitoring, Dependabot, CI verification, planned dependency/security scanning |
| Availability | Connection pooling/pre-ping/recycling, Redis-backed rate limiting, bounded queries, readiness checks, operational recovery requirements |

## API Security Top 10 coverage

### API1 — Broken Object Level Authorization

Endpoints using object identifiers must verify ownership or an explicitly authorized administrative relationship. Cross-user risk-assessment access is denied by default.

### API2 — Broken Authentication

JWTs use explicit issuer/audience validation, short access-token lifetimes, token-version revocation, UUID JTIs, and login throttling/account lockout.

### API3 — Broken Object Property Level Authorization

API payloads use explicit fields and allow-lists rather than blindly applying client dictionaries to ORM models.

### API4 — Unrestricted Resource Consumption

Rate limits, maximum request sizes, ingestion batch limits, bounded pagination, bounded analytics queries, and database indexes reduce resource-exhaustion risk.

### API5 — Broken Function Level Authorization

Privileged functions use server-side role checks. Administrative routes require the admin role.

### API6 — Sensitive Business Flows

Authentication, registration, AI requests, risk assessment, wearable ingestion, referrals, and notification mutations are rate-limited and validated.

### API7 — SSRF

External integrations must be implemented behind explicit adapters. User-controlled URLs must never be fetched without an allow-list and SSRF-safe network policy.

### API8 — Security Misconfiguration

Production configuration rejects unsafe defaults such as SQLite and the development secret key. Security headers, request limits, and secure transport controls are applied centrally.

### API9 — Improper Inventory Management

The versioned /api/v1 boundary is the supported API surface. The legacy /api/v0 surface returns 410 Gone.

### API10 — Unsafe Consumption of APIs

Third-party systems are isolated behind vendor-neutral integration ports. External responses are treated as untrusted data and must be validated before entering clinical workflows.

## Production-only verification

Code-level controls are not sufficient by themselves. Before clinical production, the deployment must additionally complete:

1. PostgreSQL migration rehearsal.
2. Redis failover/availability testing.
3. Backup and restore drill.
4. Load and concurrency testing.
5. Dependency and SAST scanning.
6. Threat modelling.
7. Penetration testing.
8. PII/log review.
9. Incident-response exercise.
10. Clinical validation and regulatory review where applicable.

## Clinical safety

Security controls must never be used to imply clinical validity. Experimental biosensing remains research-stage until prospective validation establishes evidence for a specific intended use.