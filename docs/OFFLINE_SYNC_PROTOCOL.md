# Offline Sync Protocol

LiverWatch field workflows are designed for intermittent connectivity. Clients create immutable operations locally, group them into envelopes, and retry until acknowledged.

## Rules
1. Every operation has a globally unique operation_id.
2. Payloads are canonicalised and checksummed before transmission.
3. The server treats retries as idempotent.
4. Clinical timestamps describe when a measurement occurred, not when it synced.
5. Conflict resolution preserves provenance and never silently overwrites a validated clinical observation.
6. Authentication, consent and authorization are rechecked when data is accepted server-side.

The protocol is transport-neutral and can be implemented by an approved mobile client or store-and-forward gateway without changing the clinical data contract.
