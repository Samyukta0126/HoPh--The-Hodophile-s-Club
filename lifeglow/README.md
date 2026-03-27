# LifeGLOW - Predictive Burnout Monitoring System

> **Detect burnout before it happens. Prescribe the fix. Protect individual privacy.**

LifeGLOW is a production-ready MVP for predicting healthcare worker burnout via EHR audit logs and shift patterns, then issuing prescriptive nudges to unit managers. No new hardware required—operates in read-only mode against existing hospital data infrastructure.

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Compliance](#compliance--security)
- [Documentation](#documentation)
- [12-Week Pilot Roadmap](#pilot-roadmap)

---

## Overview

### Problem Statement
Healthcare worker burnout is at crisis levels (45-60% of nurses affected). Current systems are **reactive**—identifying burnout only after resignation or medical leave. LifeGLOW shifts to **predictive detection**, identifying risk 2-4 weeks before critical thresholds.

### Core Approach
1. **Ingest** FHIR R4 AuditEvent resources from existing EHR
2. **Score** burnout risk using weighted rule-based algorithm (0-100 scale)
3. **Alert** unit managers with prescriptive nudges (aggregated data only)
4. **Protect** individual privacy via differential privacy and threshold-gated access

### Key Differentiators
- ✅ **Privacy-first**: Individual data never exposed unless Critical threshold (>85) crossed
- ✅ **Actionable**: Prescriptive recommendations, not just dashboards
- ✅ **Compliant**: HIPAA & GDPR by design (AES-256, TLS 1.3, RBAC, k-anonymity)
- ✅ **Lightweight**: No sensors, cameras, or workflow changes required

---

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data          │     │   Backend        │     │   Storage       │     │   Presentation  │
│   Ingestion     │────▶│   Processing     │────▶│   Layer         │────▶│   Layer         │
│                 │     │                  │     │                 │     │                 │
│ • FHIR R4 CSV   │     │ • FastAPI        │     │ • PostgreSQL    │     │ • React +       │
│ • FHIR API      │     │ • Burnout Engine │     │ • TimescaleDB   │     │   Tailwind      │
│ • Mock Generator│     │ • Alert Engine   │     │ • Encryption    │     │ • 3 Components  │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

**See full architecture diagram:** [`docs/02_system_architecture.md`](docs/02_system_architecture.md)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with TimescaleDB extension

### Backend Setup

```bash
cd lifeglow/backend

# Install dependencies
pip install fastapi uvicorn pydantic python-jose[cryptography] passlib

# Initialize database
psql -U postgres -f schema.sql

# Run burnout engine tests
python burnout_engine.py

# Start API server
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd lifeglow/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Dashboard available at: `http://localhost:3000`

### Generate Mock Data

```bash
cd lifeglow/data

# Generate test dataset (100 nurses, 30 days)
python mock_ehr_gen.py

# Output: data/mock_ehr_data.csv (~2900 records)
```

---

## Project Structure

```
lifeglow/
├── backend/
│   ├── schema.sql              # PostgreSQL + TimescaleDB schema
│   ├── burnout_engine.py       # Weighted scoring algorithm
│   └── api.py                  # FastAPI REST endpoints
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main dashboard component
│   │   ├── index.css           # Tailwind styles
│   │   └── components/
│   │       ├── RiskHeatmap.jsx        # Unit risk grid
│   │       ├── PredictiveNudge.jsx    # Manager recommendations
│   │       └── StupidStuffTracker.jsx # Workflow waste tracker
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── mock_ehr_gen.py         # FHIR R4 mock data generator
│
└── docs/
    ├── 01_executive_summary.md  # High-level overview
    ├── 02_system_architecture.md # Mermaid.js diagrams
    ├── 08_compliance_security.md # HIPAA/GDPR safeguards
    └── 09_pilot_roadmap.md      # 12-week implementation plan
```

---

## Key Features

### 1. Burnout Scoring Engine

Weighted algorithm producing 0-100 risk score based on four signals:

| Signal | Weight | Trigger Condition |
|--------|--------|-------------------|
| Pajama Time | 30% | Notes filed >2 hrs after shift end |
| Shift Overrun | 30% | Clock-out >45 mins past shift end |
| Recovery Debt | 25% | 3+ consecutive shifts OR <10 hrs rest |
| PTO Stagnation | 15% | Zero PTO days in 60 days |

**Risk Levels:**
- 🟢 Low: 0-39
- 🟡 Medium: 40-64
- 🟠 High: 65-84
- 🔴 Critical: 85-100

### 2. Privacy Protection

- **k-Anonymity**: Manager queries return aggregated data only (minimum k=5 workers)
- **Threshold Gating**: Individual data unlocked ONLY when score >85 (Critical)
- **Hashed Identifiers**: Worker names stored as SHA-256 hashes, never plaintext
- **Immutable Audit Logs**: All access logged, no deletions allowed

### 3. Dashboard Components

#### RiskHeatmap
Grid view of all units color-coded by risk level with trend indicators.

#### PredictiveNudge
Auto-generated, actionable recommendations sorted by urgency.
> Example: "Unit 4B is at 85% risk — recommend 1 float nurse for Thursday"

#### StupidStuffTracker
Identifies wasteful EHR actions across the department.
> Example: "Nurses clicking through 6 unnecessary alert screens per shift"

---

## REST API Specification

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/telemetry` | Ingest EHR audit events | API Key |
| GET | `/api/v1/alerts` | Return unit-level alerts | JWT + RBAC |
| POST | `/api/v1/interventions` | Log manager nudges | JWT + RBAC |
| GET | `/api/v1/scores/{unit_id}` | Fetch aggregated scores | JWT + RBAC |
| GET | `/api/v1/health` | System health check | Internal |

**Full API docs:** [`backend/api.py`](backend/api.py)

---

## Compliance & Security

| Safeguard | Standard | Implementation |
|-----------|----------|----------------|
| AES-256 Encryption | HIPAA/GDPR | Column-level via pgcrypto |
| TLS 1.3 | HIPAA/GDPR | NGINX + FastAPI middleware |
| RBAC | HIPAA §164.308 | JWT + role checker |
| Audit Logs | HIPAA §164.312 | Immutable append-only |
| k-Anonymity | GDPR Art. 25 | Database functions enforce k≥5 |
| Threshold Gating | HIPAA Safe Mode | Score >85 check at DB layer |

**Full compliance documentation:** [`docs/08_compliance_security.md`](docs/08_compliance_security.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [Executive Summary](docs/01_executive_summary.md) | High-level logic, problem statement, approach |
| [System Architecture](docs/02_system_architecture.md) | Mermaid.js flow diagrams |
| [Database Schema](backend/schema.sql) | Full SQL with Differential Privacy |
| [Burnout Engine](backend/burnout_engine.py) | Python scoring algorithm |
| [REST API](backend/api.py) | FastAPI endpoints with schemas |
| [Mock Data Generator](data/mock_ehr_gen.py) | FHIR R4 CSV generator |
| [Compliance](docs/08_compliance_security.md) | HIPAA/GDPR safeguards |
| [Pilot Roadmap](docs/09_pilot_roadmap.md) | 12-week delivery plan |

---

## Pilot Roadmap

### Phase Timeline

| Phase | Weeks | Objective | Deliverable |
|-------|-------|-----------|-------------|
| Discovery | 1-2 | Shadow workflows; identify units | Security packet + sign-off |
| Design | 3-4 | Map data flow; prototype | Clickable prototype |
| Build | 5-9 | Ship MVP | HIPAA-compliant baseline |
| Pilot | 10-12 | Run with 2 units | Outcome report |

### Success Metrics (12-Week Pilot)
- 📉 10% reduction in late shift stays
- 📈 15% improvement in PTO utilization
- 🎯 80%+ early identification of at-risk staff
- 🔒 Zero privacy incidents

**Full roadmap:** [`docs/09_pilot_roadmap.md`](docs/09_pilot_roadmap.md)

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 + TimescaleDB |
| Frontend | React 18 + Tailwind CSS |
| Security | AES-256, TLS 1.3, JWT + RBAC |
| Compliance | FHIR R4, HIPAA Safe Harbor, GDPR Art. 25 |

---

## License

© 2025 LifeGLOW Health Systems. All rights reserved.

**Confidentiality Notice:** This software contains proprietary algorithms and methods for healthcare workforce analytics. Unauthorized use, reproduction, or distribution is prohibited.

---

## Contact

- **Security:** security@lifeglow.health
- **Privacy:** privacy@lifeglow.health
- **Support:** support@lifeglow.health

---

*Built with ❤️ for healthcare workers everywhere*
