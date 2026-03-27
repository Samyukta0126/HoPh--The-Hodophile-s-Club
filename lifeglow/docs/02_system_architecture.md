# LifeGLOW System Architecture

## Data Flow Diagram (Mermaid.js)

```mermaid
flowchart LR
    subgraph Data_Ingestion["Data Ingestion Layer"]
        A[FHIR R4 AuditEvent CSV]
        B[FHIR API Gateway]
        C[Mock Data Generator]
    end

    subgraph Backend_Processing["Backend Processing Layer - FastAPI"]
        D[Ingestion Service]
        E[Burnout Scoring Engine]
        F[Alert Engine]
        G[Privacy Filter]
    end

    subgraph Storage["Storage Layer - PostgreSQL + TimescaleDB"]
        H[(workers)]
        I[(shift_events)]
        J[(ehr_audit_logs)]
        K[(burnout_scores hypertable)]
        L[(interventions)]
        M[(audit_logs)]
    end

    subgraph Presentation["Presentation Layer - React Dashboard"]
        N[RiskHeatmap Component]
        O[PredictiveNudge Component]
        P[StupidStuffTracker Component]
    end

    %% Data Flow Arrows
    A -->|FHIR JSON| D
    B -->|FHIR JSON| D
    C -->|CSV Import| D
    
    D -->|parsed_worker_data| E
    E -->|risk_score 0-100| F
    E -->|score + trigger| K
    F -->|alert_payload unit_id| G
    G -->|aggregated_only| N
    G -->|nudge_recommendations| O
    
    D -->|normalized_records| I
    D -->|audit_events| J
    I -->|shift patterns| E
    J -->|EHR activity| E
    
    F -->|intervention_log| L
    D -->|access_log| M
    E -->|calculation_log| M
    
    O -->|action_taken| L
    N -->|unit_click| G
    P -->|waste_metrics| G

    %% Styling
    style Data_Ingestion fill:#e3f2fd,stroke:#1976d2
    style Backend_Processing fill:#fff3e0,stroke:#f57c00
    style Storage fill:#e8f5e9,stroke:#388e3c
    style Presentation fill:#f3e5f5,stroke:#7b1fa2
```

## Layer Descriptions

### 1. Data Ingestion Layer
- **Input**: FHIR R4 AuditEvent resources (CSV or API)
- **Components**: Mock data generator for testing, FHIR API gateway for production
- **Output**: Normalized JSON to backend processing

### 2. Backend Processing Layer (FastAPI)
- **Ingestion Service**: Validates FHIR schema, normalizes data
- **Burnout Scoring Engine**: Applies weighted algorithm (Section 4)
- **Alert Engine**: Determines risk level, generates nudges
- **Privacy Filter**: Enforces aggregation rules, threshold gating

### 3. Storage Layer (PostgreSQL + TimescaleDB)
- **Relational Tables**: workers, shift_events, ehr_audit_logs, interventions
- **Time-Series**: burnout_scores as hypertable (partitioned by week)
- **Audit Trail**: Immutable append-only audit_logs table
- **Encryption**: AES-256 column-level encryption on sensitive fields

### 4. Presentation Layer (React + Tailwind)
- **RiskHeatmap**: Unit-level grid view with color-coded risk
- **PredictiveNudge**: Actionable recommendations sorted by urgency
- **StupidStuffTracker**: Wasteful EHR action identification

## Security Boundaries
- **TLS 1.3**: All inter-layer communication encrypted
- **RBAC**: JWT tokens with role claims (Manager/Admin/Executive)
- **Data Minimization**: Only aggregated data crosses to presentation layer
- **Threshold Gate**: Individual data unlocked only when score > 85
