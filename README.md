# LiverWatch

<div align="center">

**Longitudinal Liver-Health Intelligence & Care-Support Platform**

A Uganda-focused health technology platform designed to connect patient monitoring, community screening, clinical review, longitudinal records, referrals, and future validated wearable/biosensor integrations.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/CI-Tests%20Required-informational.svg)](#testing)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Copyright & Ownership

**Copyright © 2026 Kweezi Perez Christopher. All rights reserved to the copyright owner, subject to the permissions granted by the MIT License below.**

The original LiverWatch source code, system architecture, original documentation, original application design, and other original project materials in this repository are copyrighted works of **Kweezi Perez Christopher**. The copyright notice must not be removed from copies or substantial portions of the project. Third-party libraries, frameworks, models, APIs, and other dependencies remain the property of their respective authors and are governed by their own licenses.

LiverWatch is distributed under the **MIT License**. The MIT License grants the permissions described in `LICENSE`; it does not transfer copyright ownership of the original LiverWatch work.

## What LiverWatch Is

LiverWatch is being developed as a **health monitoring and clinical-support infrastructure**, not simply a health-information website.

The platform is intended to help people and healthcare teams answer practical questions over time:

- What health measurements have changed?
- Is a person's current pattern different from their established baseline?
- What risk factors and symptoms are present?
- Does the pattern warrant follow-up or referral?
- Has a referral been acknowledged and completed?
- What happened after the patient was screened?
- Can validated external devices eventually contribute reliable measurements?
- Can anonymised longitudinal data support research and public-health planning?

The web application is one interface to this system. The long-term product is the secure data, monitoring, decision-support, referral and integration platform underneath it.

## Clinical Safety Boundary

LiverWatch is **not an autonomous diagnostic system** and does not replace a licensed healthcare professional.

Risk assessments are intended for screening and care-support purposes. Clinical decisions must be made by appropriately qualified healthcare professionals using appropriate clinical evidence.

LiverWatch will not claim that:

- a skin tag directly measures liver function;
- an experimental wearable measurement is a validated clinical biomarker;
- an AI model can diagnose liver disease;
- a device can replace laboratory testing or clinical assessment.

Future sweat, interstitial-fluid and other biosensing capabilities will remain explicitly experimental until supported by appropriate validation evidence.

---

# Current Architecture

```
                    LIVERWATCH
                         |
        +----------------+----------------+
        |                |                |
     Patient            CHW           Clinician
     interface        workflow          portal
        |                |                |
        +----------------+----------------+
                         |
                    Secure API
                         |
              Clinical Data Platform
                         |
        +----------------+----------------+
        |                |                |
   Risk Support      Longitudinal      Referral
     Engine            Records          Workflow
        |                |                |
        +----------------+----------------+
                         |
              External Integration Layer
                         |
       +----------------+----------------+
       |                |                |
   Laboratories     Healthcare        Devices /
                    facilities         sensors*
```

`*` Device and biosensor outputs are treated according to their validation status.

---

# What Exists in the Codebase

The repository already contains foundations for:

- User authentication and authorization
- Patient records
- CHW/health-worker roles
- Clinician and researcher roles
- Consent management
- Audit records
- Risk assessments
- Screening results
- Longitudinal records
- Healthcare facilities
- Referrals
- Wearable-device records
- Biomarker types
- Notifications
- Health tracking
- AI agent infrastructure
- Healthcare discovery
- Community features
- Administrative workflows
- Database migrations
- Security controls
- Automated tests

The current implementation is a foundation, not a claim that every future capability is already production-ready.

---

# Development Roadmap

The transformation is deliberately divided into independently merged phases.

| Phase | Objective | Status |
|---|---|---|
| 0 | Foundation reset & production baseline | Complete |
| 1 | Test, CI & reliability foundation | In progress |
| 2 | Secure clinical data core | Complete |
| 3 | Liver risk & clinical decision support | Complete |
| 4 | Patient monitoring & alerting | Complete |
| 5 | CHW/VHT field system | Complete |
| 6 | Clinician & healthcare facility platform | Complete |
| 7 | Device & wearable integration platform | Complete |
| 8 | Non-invasive biosensing research interface | Complete |
| 9 | Clinical validation & evidence platform | Complete |
| 10 | Intelligence, population health & research | Complete |
| 11 | Production operations, scale & governance | Complete |
| 12 | External integration completion | Complete |

See **[docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md)** for the detailed engineering plan, exit criteria, branch protocol and clinical boundaries.

---

# Technology Stack

## Backend

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Limiter
- Flask-Caching
- Flask-Mail
- Alembic / Flask-Migrate
- Celery / Redis
- Gunicorn

## AI / Decision Support

- Google ADK
- Google GenAI

AI is constrained to structured health-support use cases. Deterministic clinical/risk rules and their provenance remain important parts of the architecture.

## Data

- PostgreSQL for production
- SQLite for development/testing where appropriate
- Redis for caching and asynchronous workloads

## Frontend

- Jinja2
- HTML5
- CSS3
- JavaScript
- Chart.js
- Font Awesome

---

# Repository Structure

```
LiverWatch/
├── app/
│   ├── blueprints/       # HTTP routes and application interfaces
│   ├── services/         # Business and domain services
│   ├── templates/        # Jinja2 views
│   ├── static/           # CSS, JavaScript and assets
│   ├── models.py         # Domain/data models
│   ├── forms.py          # Input validation and forms
│   ├── config.py         # Environment configuration
│   └── __init__.py       # Application factory
│
├── liverwatch_agents/    # AI agent and tool architecture
├── migrations/           # Database migrations
├── tests/                # Unit, integration and security tests
├── docs/                 # Architecture, roadmap and engineering docs
├── run.py                # Development entry point
├── requirements.txt      # Python dependencies
└── pytest.ini            # Test configuration
```

---

# Local Development

## Requirements

- Python 3.9+
- pip
- Git
- PostgreSQL for production-like development
- Redis when exercising asynchronous/cache functionality

## Setup

```bash
git clone https://github.com/PerezChris99/LiverWatch.git
cd LiverWatch

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create a local environment file from the repository's environment template and configure the required values.

Then run:

```bash
python run.py
```

---

# Configuration

Production configuration should provide, at minimum, appropriate values for:

- `SECRET_KEY`
- `DATABASE_URL`
- AI provider credentials where AI functionality is enabled
- mail configuration where email is enabled
- encryption configuration for protected personal data
- Redis configuration where caching/rate limiting/background processing is enabled
- monitoring configuration where production observability is enabled

**Never commit credentials, API keys, patient information, clinical records or other secrets to Git.**

---

# Testing

Testing is a release requirement, not an optional quality step.

Run the complete suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov=app --cov=liverwatch_agents --cov-report=term-missing
```

Run a focused suite:

```bash
pytest tests/test_auth.py -v
pytest tests/test_models.py -v
pytest tests/test_api.py -v
pytest tests/test_security.py -v
pytest tests/test_agents.py -v
```

A phase is not considered complete until its relevant tests pass and the full regression suite remains green.

---

# Data & Privacy Principles

LiverWatch is designed around health data, so privacy and traceability are core engineering concerns.

The platform uses or is designed to use:

- explicit consent;
- role-based access;
- protected personal information;
- audit trails;
- data provenance;
- least-privilege access;
- validation of external measurements;
- research-specific consent and controls;
- pseudonymisation/anonymisation for appropriate research datasets.

The system should be operated in accordance with applicable Ugandan privacy, health, research and regulatory requirements.

---

# External Integrations

The core LiverWatch platform should remain vendor-neutral.

External systems may include:

### Healthcare
- Hospitals
- Clinics
- Laboratories
- Clinicians
- Community health workers
- Referral networks

### Devices
- BLE wearables
- Physiological sensors
- Sweat sensors
- Interstitial-fluid sensing systems
- Future validated liver-health monitoring devices

### Infrastructure
- SMS providers
- Email providers
- Mapping/geolocation providers
- Cloud hosting
- Error monitoring
- Device-management platforms

Integrations should be implemented through stable adapters and versioned contracts.

---

# Wearable & Biosensing Direction

A future LiverWatch device is envisioned as a **monitoring companion**, not a magic liver detector.

A validated device could eventually:

1. collect supported signals;
2. assess measurement quality;
3. transmit measurements securely;
4. compare measurements against a person's longitudinal baseline;
5. contribute data to the LiverWatch risk-support engine;
6. alert the user when a clinically meaningful pattern warrants attention;
7. support follow-up with a healthcare professional.

A vibration or phone alert can be technically straightforward. The scientifically difficult part is establishing that a non-invasive signal reliably correlates with clinically meaningful liver-health changes.

That distinction drives the development strategy.

---

# Skin Tags & Metabolic Risk

Skin tags may be investigated as **one contextual risk marker** because their presence can be associated with metabolic conditions in some populations.

They are not liver sensors.

LiverWatch may eventually record skin/metabolic observations alongside established clinical measurements, but the system will not infer liver disease from skin tags alone.

---

# Research Direction

The long-term research program can investigate non-invasive monitoring using:

- sweat;
- interstitial fluid;
- physiological signals;
- metabolic context;
- validated biochemical measurements;
- longitudinal correlations with reference laboratory tests.

Experimental measurements must remain clearly labelled until clinical validation establishes their meaning.

The intended evidence pathway is:

```
Research signal
      ↓
Calibration
      ↓
Reference laboratory comparison
      ↓
Clinical correlation
      ↓
Prospective validation
      ↓
Evidence-backed clinical use
```

---

# Branching & Release Discipline

LiverWatch uses two primary branches:

```
perez  →  Pull Request  →  main
DEV                         STABLE
```

### `perez`
Development branch. All implementation work is performed here.

### `main`
Stable branch. It receives completed phases through independently reviewed and tested pull requests.

Each phase should:

1. start from the current stable state;
2. be implemented on `perez`;
3. include tests;
4. update documentation;
5. use meaningful commits;
6. pass CI;
7. open a PR into `main`;
8. merge independently;
9. verify the resulting `main`;
10. record the completed milestone.

Example commit style:

```text
docs: establish LiverWatch production architecture
test: repair SQLAlchemy 3 test database fixtures
ci: enforce green test and migration checks
feat: introduce provenance-aware clinical observations
feat: add explainable liver risk assessment engine
feat: implement longitudinal monitoring alerts
feat: add offline CHW screening workflow
feat: add clinician referral workflow
feat: add device ingestion contracts
feat: add experimental biosensor research pipeline
ops: add production observability and recovery checks
```

---

# Definition of Done

A feature or phase is complete only when:

- the implementation exists;
- automated tests cover it;
- the regression suite remains green;
- migrations are verified;
- security implications are addressed;
- clinical claims are appropriately bounded;
- documentation matches the implementation;
- observability is adequate;
- the change is committed to `perez`;
- the phase is merged independently into `main`;
- the resulting stable branch is verified.

---

# Project Philosophy

**Useful in the real world. Honest about what is known. Safe about what is not. Built for production.**

LiverWatch should become infrastructure that helps people get from **measurement → understanding → appropriate action → clinical follow-up**, rather than another health website that simply displays information.

---

## License

**Copyright © 2026 Kweezi Perez Christopher.**

The original LiverWatch work is copyrighted and is licensed under the MIT License. See [LICENSE](LICENSE) for the complete license text. Third-party components retain their respective copyrights and licenses.

For security vulnerabilities, see [SECURITY.md](SECURITY.md).
