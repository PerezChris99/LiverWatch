# External Integration Boundaries

LiverWatch core is vendor-neutral. SMS, email, laboratory systems, healthcare facilities, device gateways, maps and other external services connect through ports/adapters.

External failures must not corrupt the clinical data model. Each adapter should provide timeouts, retries where safe, idempotency keys, structured errors and observability. Credentials belong in deployment secret management, never in source control.

The remaining real-world dependencies are intentionally external: licensed healthcare professionals, healthcare facilities, laboratories, device hardware, clinical validation cohorts and regulatory approvals.
