# LifeGLOW Compliance & Security Safeguards

## Overview
LifeGLOW is designed from the ground up to meet HIPAA and GDPR requirements for healthcare data processing. This document outlines all security controls, privacy safeguards, and compliance measures implemented in the system.

---

## 1. Data Encryption

### 1.1 AES-256 Encryption at Rest (HIPAA §164.312(a)(2)(iv))

**Implementation:**
- All sensitive columns in PostgreSQL encrypted using `pgcrypto` extension
- Burnout scores encrypted at database level
- Worker identifiers stored as SHA-256 hashes only (never plaintext)

```sql
-- Column-level encryption example
SELECT pgp_sym_encrypt(sensitive_data, 'encryption_key');
SELECT pgp_sym_decrypt(encrypted_column, 'encryption_key');
```

**Key Management:**
- Encryption keys stored in secure key management system (AWS KMS / HashiCorp Vault)
- Keys rotated quarterly
- No keys stored in application code or configuration files

### 1.2 TLS 1.3 Encryption in Transit (HIPAA §164.312(e)(1))

**Implementation:**
- All API traffic enforced over HTTPS with TLS 1.3
- NGINX reverse proxy configured with modern cipher suites
- Certificate pinning for internal service communication

**NGINX Configuration:**
```nginx
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
ssl_prefer_server_ciphers off;
add_header Strict-Transport-Security "max-age=63072000" always;
```

---

## 2. Access Control

### 2.1 Role-Based Access Control (RBAC) (HIPAA §164.308(a)(4))

**Three Defined Roles:**

| Role | Permissions | Data Access |
|------|-------------|-------------|
| **Manager** | View assigned unit only, log interventions | Aggregated unit data only (k≥5) |
| **Admin** | Full system access, all units | Individual data when score >85 |
| **Executive** | Aggregate reports, audit logs | Department-level aggregates only |

**Implementation:**
```python
# FastAPI dependency for role checking
def require_role(required_roles: List[str]):
    async def role_checker(user: Dict = Depends(verify_jwt_token)) -> Dict:
        if user['role'] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
```

### 2.2 JWT Authentication

**Token Structure:**
```json
{
  "sub": "user-uuid",
  "role": "manager",
  "unit_id": "ICU",
  "exp": 1704067200,
  "iat": 1704063600
}
```

**Security Measures:**
- Tokens expire after 1 hour
- Refresh tokens required for extended sessions
- Token binding to client IP address

---

## 3. Privacy Protection

### 3.1 HIPAA Safe Mode - Threshold-Gated Access

**Rule:** Individual worker data is NEVER exposed to managers unless burnout score exceeds Critical threshold (>85).

**Database-Level Enforcement:**
```sql
CREATE FUNCTION get_critical_individuals(unit_id VARCHAR)
RETURNS TABLE (worker_id UUID, score INTEGER, ...) AS $$
BEGIN
    RETURN QUERY
    SELECT bs.worker_id, bs.score, ...
    FROM burnout_scores bs
    WHERE bs.unit_id = $1
      AND bs.score > 85;  -- HARD THRESHOLD
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Application Layer Defense:**
```python
# Privacy filter in API layer
if result.risk_level != RiskLevel.CRITICAL:
    # Never expose individual data
    return aggregate_only_response
```

### 3.2 Differential Privacy - k-Anonymity (GDPR Art. 25)

**Rule:** Manager-facing queries return aggregated data ONLY when minimum k=5 workers present.

**Implementation:**
```sql
-- Materialized view with k-anonymity enforcement
CREATE MATERIALIZED VIEW aggregated_unit_scores AS
SELECT unit_id, AVG(score), ...
FROM burnout_scores
GROUP BY unit_id
HAVING COUNT(*) >= 5;  -- k-anonymity threshold
```

**Query-Time Check:**
```python
def calculate_unit_aggregate_risk(worker_results, min_k_anonymity=5):
    if len(worker_results) < min_k_anonymity:
        return None  # Privacy protection - insufficient data
    # Return aggregates only
```

### 3.3 Data Minimization (GDPR Art. 5(1)(c))

**Principle:** Collect only what is necessary, retain only as long as needed.

**Implementation:**
- Worker names never stored - only hashed identifiers
- PTO data aggregated to 60-day window (not historical)
- Shift data retained for 90 days rolling window
- Audit logs retained for 6 years (HIPAA requirement)

---

## 4. Audit Controls

### 4.1 Immutable Audit Logs (HIPAA §164.312(b))

**Requirements Met:**
- Every data access logged
- No record can be deleted or modified (append-only)
- User identity, timestamp, action, and resource captured

**Schema:**
```sql
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id UUID,
    resource_type VARCHAR(50) NOT NULL,
    action VARCHAR(20) CHECK (action IN ('SELECT','INSERT','UPDATE','DELETE')),
    ip_address INET,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger prevents deletes
CREATE TRIGGER trg_audit_all
    BEFORE DELETE ON any_table
    FOR EACH ROW EXECUTE FUNCTION prevent_delete();
```

### 4.2 Access Logging

**Logged Events:**
- All API requests (endpoint, method, response code)
- Database queries on sensitive tables
- Authentication attempts (success/failure)
- Data exports or bulk operations

---

## 5. Technical Safeguards Summary

| Safeguard | Standard | Implementation | Status |
|-----------|----------|----------------|--------|
| AES-256 Encryption | HIPAA/GDPR | Column-level via pgcrypto | ✅ Implemented |
| TLS 1.3 | HIPAA/GDPR | NGINX + FastAPI middleware | ✅ Implemented |
| RBAC | HIPAA §164.308 | JWT + role checker | ✅ Implemented |
| Audit Logs | HIPAA §164.312 | Immutable append-only | ✅ Implemented |
| k-Anonymity | GDPR Art. 25 | Database functions enforce k≥5 | ✅ Implemented |
| Threshold Gating | HIPAA Safe Mode | Score >85 check at DB layer | ✅ Implemented |
| Session Timeout | HIPAA §164.312 | 1-hour JWT expiry | ✅ Implemented |
| Input Validation | OWASP | Pydantic schema validation | ✅ Implemented |

---

## 6. Data Protection Impact Assessment (DPIA) - GDPR Art. 35

### 6.1 Data Processing Activities

| Data Type | Purpose | Legal Basis | Retention |
|-----------|---------|-------------|-----------|
| Shift times | Burnout calculation | Legitimate interest | 90 days |
| EHR audit logs | Pattern detection | Legitimate interest | 90 days |
| PTO records | Recovery debt scoring | Legitimate interest | 60 days |
| Burnout scores | Risk prediction | Consent (via employer) | 90 days |
| Intervention logs | Quality improvement | Legitimate interest | 6 years |

### 6.2 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Individual exposure | Low | High | Threshold gating, k-anonymity |
| Data breach | Low | High | AES-256, TLS 1.3, minimal retention |
| Function creep | Medium | Medium | Purpose limitation in policy |
| Algorithmic bias | Low | Medium | Regular model audits, human review |

### 6.3 Data Subject Rights (GDPR Art. 15-22)

**Procedures Established:**
- Right to access: Export all data for specific worker (via Admin)
- Right to rectification: Correct inaccurate shift/EHR data at source
- Right to erasure: Delete worker hash and associated scores (within retention limits)
- Right to object: Opt-out of non-essential processing (PTO analysis)

---

## 7. Business Associate Agreement (BAA) Requirements

**LifeGLOW commits to:**
1. Use PHI only for specified purposes (burnout monitoring)
2. Implement appropriate safeguards (as documented herein)
3. Report breaches within 60 days (HIPAA §164.410)
4. Ensure subcontractors comply with same standards
5. Make records available to HHS upon request
6. Return/destroy PHI at contract termination

---

## 8. Incident Response Plan

### 8.1 Breach Notification Timeline

```
Discovery → Containment (24h) → Assessment (48h) → Notification (60 days max)
```

### 8.2 Contact Points

- **Security Officer:** security@lifeglow.health
- **Privacy Officer:** privacy@lifeglow.health
- **Emergency:** +1-XXX-XXX-XXXX (24/7 hotline)

---

## 9. Compliance Certification Checklist

- [ ] AES-256 encryption verified by third-party audit
- [ ] TLS 1.3 configuration tested with SSL Labs (A+ rating)
- [ ] Penetration testing completed annually
- [ ] Staff HIPAA training completed
- [ ] BAA signed with all covered entities
- [ ] DPIA documented and approved
- [ ] Incident response drill conducted quarterly
- [ ] Backup and disaster recovery tested

---

*Document Version: 1.0 | Last Updated: 2025-01-01 | Next Review: 2025-04-01*
