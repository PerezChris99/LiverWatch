# Production Readiness

A production deployment requires more than passing application tests.

Required controls include: strong secret management, PostgreSQL migrations, encrypted protected data, TLS, secure cookies, rate limiting, audit logging, backups and restore drills, structured logs, error monitoring, least-privilege service accounts, dependency updates, incident response and a tested rollback path.

The application readiness check is intentionally conservative: missing critical configuration means not ready. CI is a release gate when GitHub Actions is operational; current Actions infrastructure issues are tracked separately and must not be hidden by weakening tests.
