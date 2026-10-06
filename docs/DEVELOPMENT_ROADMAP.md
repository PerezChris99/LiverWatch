# LiverWatch Development Roadmap

## Mission

LiverWatch is being transformed from a liver-health web application into a **clinical-support and longitudinal liver-health monitoring platform** that can eventually connect patients, community health workers, clinicians, laboratories, healthcare facilities, research programs, and external wearable/biochemical sensing devices.

The software must remain useful without proprietary hardware. Hardware and external healthcare services are integrations, not the core intelligence of LiverWatch.

> **Clinical boundary:** LiverWatch provides screening support, trend detection, education, monitoring, and referral support. It must not claim to diagnose liver disease or replace a licensed clinician.

---

## Target End State

```
Patients / CHWs / Clinicians / Researchers
                 |
                 v
        LiverWatch Applications
                 |
                 v
          Secure API Platform
                 |
     +-----------+-----------+
     |                       |
     v                       v
Clinical Data           Device Data
Labs / symptoms         Wearables / BLE
risk factors            sweat / ISF*
     |                       |
     +-----------+-----------+
                 v
       LiverWatch Intelligence
       - validation
       - risk patterns
       - trend analysis
       - alerts
       - referral rules
                 |
        +--------+--------+
        |        |        |
        v        v        v
     Patient  Clinician  Research
      care     review     analytics

* Only when scientifically and clinically validated.
```

---

# Engineering Rules

1. **Perez is the development branch.** All implementation work lands on `perez`.
2. **Main is the stable branch.** Every phase is merged independently through its own pull request.
3. **One phase = one mergeable milestone.** No giant migration branch.
4. **Tests are a release gate.** A phase is not complete until its relevant tests pass.
5. **No fake clinical capability.** Unsupported biomarkers, diagnoses, predictions, or device claims must not be presented as real.
6. **External dependencies stay behind adapters.** Labs, facilities, SMS, maps, payment providers, wearable vendors, and future biosensors must not be hard-coded into the core domain.
7. **Every important clinical decision is explainable and auditable.**
8. **Consent and data minimisation are first-class architecture requirements.**
9. **Offline/low-connectivity workflows are considered a primary Uganda use case.**
10. **Hardware is developed against a stable data contract, not the other way around.**

---

# Phase 0 — Foundation Reset & Production Baseline

**Goal:** Establish the engineering truth of the existing repository before adding new capability.

### Deliverables
- Reconcile README claims with actual implementation.
- Establish a production-readiness checklist.
- Document the target architecture and clinical safety boundary.
- Inventory existing models, routes, services, agents, migrations, integrations and tests.
- Remove obsolete documentation claims as implementation work progresses.
- Establish the definition of done for every subsequent phase.

### Exit criteria
- Architecture documented.
- Current gaps explicitly tracked.
- No documentation claims unverified functionality.
- `perez` workflow established.

---

# Phase 1 — Test, CI & Reliability Foundation

**Goal:** Make the codebase trustworthy enough to evolve safely.

### Deliverables
- Repair the Flask-SQLAlchemy 3.x test fixture problem.
- Make the complete test suite executable.
- Fix genuine application failures rather than weakening tests.
- Add regression tests for authentication, authorization, database models, API contracts and security.
- Add coverage reporting.
- Add GitHub Actions CI for every push and pull request.
- Define required checks before merging `perez` into `main`.
- Add migration consistency checks.
- Add lint/type/static checks where compatible with the existing stack.

### Exit criteria
- CI is reproducible.
- Tests are green.
- Database migrations can be checked from a clean environment.
- No known test infrastructure blockers remain.

---

# Phase 2 — Secure Clinical Data Core

**Goal:** Turn existing health records into a coherent longitudinal clinical data model.

### Deliverables
- Formal patient identity and record lifecycle.
- Clinical observations with provenance, units, timestamps and reference metadata.
- Standardised biomarker representation.
- Symptoms and risk factors as structured observations.
- Lab-result ingestion model.
- Measurement provenance: patient, CHW, clinician, laboratory, device.
- Data quality states: pending, validated, rejected, corrected.
- Immutable audit history for sensitive clinical events.
- Consent-aware access control.
- Secure PII boundaries and encryption.
- API versioning and validation.

### Core principle

A measurement is not merely a number.

It must answer:

**what, value, unit, when, who/what measured it, source, confidence/quality, and whether it has been clinically verified.**

### Exit criteria
- Longitudinal records are reliable.
- Clinical data can be traced to its source.
- Access and audit controls are test-covered.

---

# Phase 3 — Liver Risk & Clinical Decision Support Engine

**Goal:** Replace scattered health logic with a deterministic, testable risk-support engine.

### Deliverables
- Explicit risk-factor model.
- Liver-health screening rules.
- Biomarker trend analysis.
- Baseline deviation detection.
- Missing-data handling.
- Measurement-quality handling.
- Urgency classification.
- Referral recommendation rules.
- Explainable risk output.
- Clinical disclaimer enforcement.
- Rule/version provenance so historical assessments remain reproducible.

### AI role

AI may explain, summarise, educate and assist with pattern review.

AI must not silently invent clinical thresholds or make an unsupported diagnosis.

### Exit criteria
- Same input produces reproducible risk output.
- Every risk result has reasons and source data.
- Rules are independently unit tested.

---

# Phase 4 — Patient Monitoring & Alerting

**Goal:** Make LiverWatch useful between clinic visits.

### Deliverables
- Personal baseline.
- Longitudinal trend dashboard.
- Measurement reminders.
- Follow-up schedules.
- Alert severity model.
- In-app alerts.
- Email/SMS adapter interfaces.
- Alert acknowledgement.
- Escalation rules.
- Safety-net messages for urgent symptoms.
- Alert fatigue controls.

### Exit criteria
A patient can be monitored over time and understand:
- what changed,
- why it matters,
- what action is recommended,
- and whether clinical review is needed.

---

# Phase 5 — CHW / VHT Field System

**Goal:** Make LiverWatch practical for Uganda's community-health workflow.

### Deliverables
- CHW/VHT patient registration.
- Offline-first screening workflow.
- Deferred synchronization.
- Conflict handling.
- Low-bandwidth payloads.
- Household/community follow-up queues.
- Referral creation.
- Referral status tracking.
- Facility handoff.
- Follow-up/outcome capture.
- Role-based access by geography and assignment.

### Exit criteria
A CHW can complete a screening visit with unreliable connectivity and synchronise safely later.

---

# Phase 6 — Clinician & Healthcare Facility Platform

**Goal:** Connect screening to real healthcare action.

### Deliverables
- Clinician dashboard.
- Patient timeline.
- Referral inbox.
- Referral acknowledgement.
- Clinical review workflow.
- Lab result review.
- Follow-up/outcome recording.
- Facility directory and service capability model.
- Secure clinician notes.
- Role/permission enforcement.
- External facility integration adapters.

### External boundary

Actual diagnosis, treatment, laboratory processing and clinical care remain with licensed healthcare professionals and healthcare facilities.

### Exit criteria
A referral can move from community screening to facility review and back into longitudinal monitoring.

---

# Phase 7 — Device & Wearable Integration Platform

**Goal:** Make LiverWatch hardware-ready without pretending that unvalidated sensors are clinically meaningful.

### Deliverables
- Device registry.
- Device ownership/assignment.
- Device lifecycle state.
- Secure device authentication.
- BLE/mobile ingestion contract.
- Measurement packet schema.
- Timestamp synchronisation.
- Calibration metadata.
- Sensor quality indicators.
- Battery/connectivity status.
- Device event logs.
- Firmware/version provenance.
- Device-to-patient association lifecycle.

### Exit criteria
A validated external device can send measurements into LiverWatch through a stable API without changing the core clinical domain.

---

# Phase 8 — Non-Invasive Biosensing Research Interface

**Goal:** Create the software infrastructure for future sweat/interstitial-fluid or other biosensing research.

This phase is deliberately separated from ordinary wearable integration.

### Candidate research signals
- Sweat biomarkers.
- Interstitial-fluid biomarkers.
- Electrolytes/hydration signals.
- Inflammatory/metabolic markers.
- Physiological signals that may provide contextual information.

### Deliverables
- Research-only biomarker namespace.
- Experimental sensor ingestion.
- Calibration records.
- Reference-lab pairing.
- Sensor-vs-lab comparison datasets.
- Measurement quality metadata.
- Experimental cohort tracking.
- Research consent.
- Anonymisation/pseudonymisation.
- Study protocol metadata.

### Critical rule

A research sensor output is labelled **experimental** until clinical validation establishes what it means.

### Exit criteria
LiverWatch can support a formal sensor-validation study without presenting experimental measurements as clinical diagnoses.

---

# Phase 9 — Clinical Validation & Evidence Platform

**Goal:** Turn promising monitoring signals into evidence.

### Deliverables
- Study participant management.
- Reference laboratory measurements.
- Prospective longitudinal datasets.
- Sensor calibration/validation workflows.
- Statistical evaluation interfaces.
- Sensitivity/specificity analysis support.
- False-positive/false-negative tracking.
- Outcome capture.
- Research audit trail.
- Dataset export under consent controls.

### External dependencies
- Research institutions.
- Laboratories.
- Clinicians.
- Ethics approval.
- Study participants.
- Validated hardware.

### Exit criteria
Claims about a device or biomarker are supported by evidence rather than assumptions.

---

# Phase 10 — Intelligence, Population Health & Research

**Goal:** Use validated longitudinal data to identify useful patterns at individual and population level.

### Deliverables
- Cohort analytics.
- Disease-risk trend research.
- Geographic patterns.
- Referral performance.
- Follow-up adherence.
- Population screening analytics.
- Research dashboards.
- De-identified datasets.
- Model evaluation pipelines.
- Bias and fairness monitoring.

### Exit criteria
LiverWatch can generate useful population-level intelligence without exposing individual patient identity.

---

# Phase 11 — Production Operations, Scale & Governance

**Goal:** Operate LiverWatch as a serious health technology system.

### Deliverables
- Production observability.
- Structured logs.
- Error tracking.
- Metrics.
- Backup/restore verification.
- Disaster recovery.
- Security monitoring.
- Rate limiting.
- Abuse detection.
- Data retention policies.
- Access reviews.
- Incident response procedures.
- Performance/load testing.
- API documentation.
- Deployment automation.
- Dependency/security scanning.

### Exit criteria
The system is operationally maintainable, observable, recoverable and secure.

---

# Phase 12 — External Integration Completion

At this point the LiverWatch software platform should be substantially complete.

The remaining dependencies should primarily be external:

### Healthcare
- Hospitals.
- Clinics.
- Laboratories.
- Clinicians.
- CHWs/VHTs.
- Referral networks.

### Hardware
- Wearable electronics.
- BLE devices.
- Biosensors.
- Firmware.
- Chargers/batteries.
- Manufacturing.

### Research
- Universities.
- Ethics committees.
- Clinical investigators.
- Validation laboratories.
- Study participants.

### Infrastructure
- SMS provider.
- Email provider.
- Maps/geocoding.
- Cloud hosting.
- Monitoring provider.
- Device-management services.

LiverWatch should integrate these through documented interfaces rather than embedding vendor-specific assumptions into the core platform.

---

# Branch & Commit Protocol

## Branches

```
main  = stable/release branch
  ^
  | Pull Request + passing CI
  |
perez = development branch
```

No direct feature development on `main`.

## Every phase follows

1. Start from current `main`.
2. Synchronise `perez`.
3. Implement the phase.
4. Add/repair tests.
5. Update documentation.
6. Run the full test suite.
7. Commit meaningful changes.
8. Push `perez`.
9. Open a PR from `perez` to `main`.
10. Verify CI.
11. Merge the PR.
12. Verify `main`.
13. Record the phase completion.
14. Continue to the next phase.

## Commit style

Commits should describe actual engineering outcomes, for example:

- `docs: establish LiverWatch production architecture`
- `test: repair SQLAlchemy 3 test database fixtures`
- `ci: enforce green test and migration checks`
- `feat: introduce provenance-aware clinical observations`
- `feat: add explainable liver risk assessment engine`
- `feat: implement longitudinal monitoring alerts`
- `feat: add offline CHW screening workflow`
- `feat: add clinician referral workflow`
- `feat: add device ingestion contracts`
- `feat: add experimental biosensor research pipeline`
- `test: add clinical validation regression coverage`
- `ops: add production observability and recovery checks`

Avoid meaningless commits such as `update stuff`, `fix things`, or giant mixed-purpose commits.

---

# Definition of Done

A phase is complete only when:

- implementation is present;
- tests cover the new behaviour;
- existing tests remain green;
- migrations are safe;
- security implications are addressed;
- clinical claims are appropriately bounded;
- documentation matches reality;
- API contracts are documented;
- observability is sufficient for the feature;
- the change is committed to `perez`;
- the PR is merged into `main`;
- the resulting `main` state is verified.

---

# Non-Goals

LiverWatch will not:

- diagnose liver disease autonomously;
- replace doctors;
- claim that skin tags directly measure liver function;
- treat experimental sweat/ISF measurements as validated clinical biomarkers;
- manufacture hardware inside the software project;
- pretend that a third-party device is medically accurate without validation.

---

# Product Vision

The finished system is not simply a website.

It is a **longitudinal liver-health intelligence and care-support platform** connecting measurements, people, clinical workflows and eventually validated non-invasive sensing.

The web application is the visible interface.

The real product is the infrastructure underneath it.
