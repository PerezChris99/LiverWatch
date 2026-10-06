# Security Policy

## Scope

LiverWatch handles health-related information and is developed with security, privacy, clinical safety, and operational resilience as first-class requirements.

Security controls are designed around the OWASP Application Security Verification Standard (ASVS), OWASP API Security Top 10, secure coding practices, least privilege, defense in depth, and fail-secure behavior.

## Reporting a Vulnerability

Do not disclose suspected vulnerabilities publicly in GitHub issues.

Please report security vulnerabilities privately to the project maintainer through the repository's configured private security reporting channel. Include:

- affected component and endpoint;
- a concise description of the vulnerability;
- reproducible steps or a proof of concept where safe;
- expected versus observed behavior;
- potential impact;
- suggested mitigation, if known.

Do not include real patient information, credentials, API keys, access tokens, or other sensitive data in a report.

## Security Expectations

Changes affecting authentication, authorization, health data, cryptography, external integrations, database migrations, or infrastructure must include appropriate tests and documentation.

Security-sensitive changes must preserve:

- object-level and function-level authorization;
- input validation and bounded resource consumption;
- CSRF protection for browser-cookie-backed state changes;
- secure session and token handling;
- audit logging without unnecessary sensitive data;
- sanitized error responses;
- encrypted/protected personal data;
- database integrity and migration safety;
- rate limiting and abuse controls;
- dependency and supply-chain hygiene.

## Clinical Safety

A security fix must not introduce unsupported clinical claims. LiverWatch is a screening and care-support platform, not an autonomous diagnostic system.

## Disclosure

The project maintainer will assess valid reports, coordinate remediation, and determine an appropriate disclosure timeline based on severity and deployment impact.
