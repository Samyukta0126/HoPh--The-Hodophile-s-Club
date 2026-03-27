"""
LifeGLOW REST API Specification
FastAPI backend with HIPAA-compliant endpoints

Endpoints:
- POST /api/v1/telemetry - Ingest EHR audit log events
- GET /api/v1/alerts - Return unit-level risk alerts
- POST /api/v1/interventions - Log manager nudges
- GET /api/v1/scores/{unit_id} - Fetch aggregated burnout scores
- GET /api/v1/health - System health check
"""

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import os

# Import burnout engine
from burnout_engine import (
    calculate_burnout_risk,
    calculate_unit_aggregate_risk,
    WorkerData,
    BurnoutResult,
    RiskLevel
)

# ============================================
# Application Setup
# ============================================

app = FastAPI(
    title="LifeGLOW API",
    description="Predictive Burnout Monitoring System - HIPAA & GDPR Compliant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# Security Configuration
# ============================================

# API Key for telemetry ingestion (from FHIR pipeline)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer token for dashboard access
security = HTTPBearer(auto_error=False)

# Valid API keys (in production, use secure key management)
VALID_API_KEYS = os.getenv("LIFEGLOW_API_KEYS", "test-api-key-123").split(",")

# Mock user database for RBAC (in production, use IdP)
USERS_DB = {
    "manager_token": {"role": "manager", "unit_id": "ICU"},
    "admin_token": {"role": "admin", "unit_id": None},
    "executive_token": {"role": "executive", "unit_id": None}
}

# ============================================
# Pydantic Models - Request Schemas
# ============================================

class RiskLevelEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class EHRAuditEvent(BaseModel):
    """FHIR R4 AuditEvent resource for EHR activity"""
    nurse_id: str = Field(..., description="Anonymized nurse identifier (UUID)")
    unit_id: str = Field(..., description="Hospital unit assignment", pattern="^[A-Z0-9]{1,10}$")
    shift_start: datetime = Field(..., description="Scheduled shift start time (ISO 8601)")
    shift_end: datetime = Field(..., description="Scheduled shift end time (ISO 8601)")
    clock_out_actual: Optional[datetime] = Field(None, description="Actual clock-out time")
    note_filed_time: Optional[datetime] = Field(None, description="Timestamp of last clinical note filed")
    pto_days_taken: int = Field(0, ge=0, le=60, description="PTO days taken in last 60 days")
    consecutive_shifts: int = Field(1, ge=1, le=14, description="Consecutive shifts without day off")
    break_taken: bool = Field(True, description="Whether meal/rest break was taken")
    alert_count: int = Field(0, ge=0, description="Number of EHR alerts encountered")
    
    @validator('shift_end')
    def validate_shift_times(cls, v, values):
        if 'shift_start' in values and v <= values['shift_start']:
            raise ValueError('shift_end must be after shift_start')
        return v


class TelemetryBatch(BaseModel):
    """Batch of EHR audit events for ingestion"""
    events: List[EHRAuditEvent] = Field(..., min_items=1, max_items=1000)
    source_system: str = Field(..., description="Source FHIR system identifier")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)


class InterventionRequest(BaseModel):
    """Manager nudge/action logging"""
    unit_id: str = Field(..., pattern="^[A-Z0-9]{1,10}$")
    recommendation_text: str = Field(..., min_length=10, max_length=500)
    action_taken: Optional[str] = Field(None, max_length=500)
    status: str = Field("pending", pattern="^(pending|accepted|declined|completed)$")


# ============================================
# Pydantic Models - Response Schemas
# ============================================

class BurnoutScoreResponse(BaseModel):
    """Individual burnout score (only exposed when Critical)"""
    worker_id: str
    score: int = Field(ge=0, le=100)
    risk_level: RiskLevelEnum
    primary_trigger: str
    calculated_at: datetime


class UnitAggregateScore(BaseModel):
    """Aggregated unit-level score (k-anonymity enforced)"""
    unit_id: str
    worker_count: int = Field(..., ge=5, description="Minimum k=5 for anonymity")
    avg_score: float = Field(ge=0, le=100)
    min_score: int
    max_score: int
    risk_distribution: Dict[str, int]
    common_triggers: List[str]
    requires_intervention: bool
    trend: Optional[str] = None


class AlertResponse(BaseModel):
    """Unit-level risk alert for dashboard"""
    unit_id: str
    avg_score: float
    risk_level: RiskLevelEnum
    critical_count: int
    high_count: int
    recommended_actions: List[str]
    generated_at: datetime


class InterventionResponse(BaseModel):
    """Logged intervention confirmation"""
    intervention_id: int
    unit_id: str
    status: str
    created_at: datetime


class HealthResponse(BaseModel):
    """System health status"""
    status: str
    uptime_seconds: float
    last_ingestion: Optional[datetime]
    total_workers: int
    total_units: int
    version: str


# ============================================
# Authentication Dependencies
# ============================================

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key for telemetry ingestion"""
    if api_key is None or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Verify JWT token and extract user info for RBAC"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    token = credentials.credentials
    
    # Mock JWT validation (in production, use proper JWT library)
    if token not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return USERS_DB[token]


def require_role(required_roles: List[str]):
    """Dependency factory for role-based access control"""
    async def role_checker(user: Dict = Depends(verify_jwt_token)) -> Dict:
        if user['role'] not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}"
            )
        return user
    return role_checker


# ============================================
# API Endpoints
# ============================================

@app.post("/api/v1/telemetry", 
          response_model=Dict[str, Any],
          tags=["Data Ingestion"],
          summary="Ingest EHR audit log events from FHIR pipeline")
async def ingest_telemetry(
    batch: TelemetryBatch,
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest batch of FHIR R4 AuditEvent resources.
    
    - Validates FHIR schema compliance
    - Calculates burnout scores for each worker
    - Stores in PostgreSQL + TimescaleDB
    - Returns ingestion summary
    
    **Authentication:** API Key required
    """
    try:
        processed_count = 0
        critical_alerts = []
        
        for event in batch.events:
            # Calculate hours between shift end and note filing
            notes_delay_hours = 0.0
            if event.note_filed_time and event.shift_end:
                delay = (event.note_filed_time - event.shift_end).total_seconds() / 3600
                notes_delay_hours = max(0, delay)
            
            # Calculate shift overrun minutes
            overrun_minutes = 0.0
            if event.clock_out_actual and event.shift_end:
                overrun = (event.clock_out_actual - event.shift_end).total_seconds() / 60
                overrun_minutes = max(0, overrun)
            
            # Prepare worker data for burnout calculation
            worker_data = WorkerData(
                worker_id=event.nurse_id,
                unit_id=event.unit_id,
                notes_filed_after_shift_hours=notes_delay_hours,
                shift_overrun_minutes=overrun_minutes,
                consecutive_overruns=event.consecutive_shifts,
                consecutive_shifts=event.consecutive_shifts,
                hours_since_last_shift=24.0 / max(1, event.consecutive_shifts),
                pto_days_taken_60d=event.pto_days_taken,
                days_since_last_pto=60 if event.pto_days_taken == 0 else 30
            )
            
            # Calculate burnout risk
            result = calculate_burnout_risk(worker_data)
            
            processed_count += 1
            
            # Track critical alerts
            if result.risk_level == RiskLevel.CRITICAL:
                critical_alerts.append({
                    'worker_id': hashlib.sha256(event.nurse_id.encode()).hexdigest()[:16],
                    'unit_id': event.unit_id,
                    'score': result.risk_score,
                    'trigger': result.primary_trigger
                })
        
        # In production: persist to database here
        
        return {
            "status": "success",
            "processed_events": processed_count,
            "critical_alerts": len(critical_alerts),
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "alerts": critical_alerts[:10]  # Limit response size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.get("/api/v1/alerts",
         response_model=List[AlertResponse],
         tags=["Dashboard"],
         summary="Return unit-level risk alerts for manager dashboard")
async def get_alerts(
    user: Dict = Depends(require_role(['manager', 'admin', 'executive'])),
    unit_id: Optional[str] = None
):
    """
    Retrieve unit-level burnout risk alerts.
    
    - Returns aggregated data only (k-anonymity enforced)
    - Managers see only their assigned unit
    - Admins/Executives see all units
    
    **Authentication:** JWT + RBAC required
    """
    # Mock alert data (in production: query database)
    mock_alerts = [
        AlertResponse(
            unit_id="ICU",
            avg_score=72.5,
            risk_level=RiskLevelEnum.HIGH,
            critical_count=2,
            high_count=5,
            recommended_actions=[
                "Review staffing levels for Thursday shift",
                "Consider float nurse support",
                "Mandate rest periods for consecutive shift workers"
            ],
            generated_at=datetime.utcnow()
        ),
        AlertResponse(
            unit_id="ED",
            avg_score=58.3,
            risk_level=RiskLevelEnum.MEDIUM,
            critical_count=0,
            high_count=3,
            recommended_actions=[
                "Monitor documentation workflow efficiency",
                "Schedule wellness check-ins"
            ],
            generated_at=datetime.utcnow()
        ),
        AlertResponse(
            unit_id="4B",
            avg_score=45.2,
            risk_level=RiskLevelEnum.MEDIUM,
            critical_count=0,
            high_count=1,
            recommended_actions=[
                "Review PTO approval patterns",
                "Encourage break compliance"
            ],
            generated_at=datetime.utcnow()
        )
    ]
    
    # Filter by unit if manager
    if user['role'] == 'manager' and user.get('unit_id'):
        mock_alerts = [a for a in mock_alerts if a.unit_id == user['unit_id']]
    
    # Filter by specific unit if requested
    if unit_id:
        mock_alerts = [a for a in mock_alerts if a.unit_id == unit_id]
    
    return mock_alerts


@app.post("/api/v1/interventions",
          response_model=InterventionResponse,
          tags=["Dashboard"],
          summary="Log a prescriptive nudge issued to a manager")
async def log_intervention(
    intervention: InterventionRequest,
    user: Dict = Depends(require_role(['manager', 'admin']))
):
    """
    Record manager action taken on burnout alert.
    
    - Logs recommendation and action taken
    - Tracks intervention effectiveness
    - Immutable audit trail (HIPAA compliant)
    
    **Authentication:** JWT + RBAC required
    """
    # Mock intervention creation (in production: insert into database)
    
    return InterventionResponse(
        intervention_id=12345,
        unit_id=intervention.unit_id,
        status=intervention.status,
        created_at=datetime.utcnow()
    )


@app.get("/api/v1/scores/{unit_id}",
         response_model=UnitAggregateScore,
         tags=["Dashboard"],
         summary="Fetch aggregated burnout score for a unit")
async def get_unit_scores(
    unit_id: str,
    user: Dict = Depends(require_role(['manager', 'admin', 'executive'])),
    days: int = 7
):
    """
    Retrieve aggregated burnout scores for a specific unit.
    
    - Enforces k-anonymity (minimum 5 workers)
    - Returns time-series data for trend analysis
    - Privacy-filtered (no individual data unless Critical)
    
    **Authentication:** JWT + RBAC required
    """
    # Verify manager has access to this unit
    if user['role'] == 'manager' and user.get('unit_id') != unit_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this unit"
        )
    
    # Mock aggregated score (in production: query database)
    return UnitAggregateScore(
        unit_id=unit_id,
        worker_count=24,
        avg_score=67.8,
        min_score=32,
        max_score=91,
        risk_distribution={
            "Low": 5,
            "Medium": 8,
            "High": 7,
            "Critical": 4
        },
        common_triggers=["Shift Overrun", "Recovery Debt"],
        requires_intervention=True,
        trend="worsening"
    )


@app.get("/api/v1/health",
         response_model=HealthResponse,
         tags=["System"],
         summary="System health check")
async def health_check():
    """
    Internal health check endpoint.
    
    - Returns system uptime
    - Last ingestion timestamp
    - Basic metrics
    
    **Authentication:** None (internal use)
    """
    # Mock health data (in production: query actual metrics)
    return HealthResponse(
        status="healthy",
        uptime_seconds=86400 * 7.5,  # 7.5 days
        last_ingestion=datetime.utcnow() - timedelta(minutes=15),
        total_workers=100,
        total_units=8,
        version="1.0.0"
    )


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Standardized error response format"""
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all error handler"""
    return {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    }


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("Starting LifeGLOW API Server...")
    print("Documentation: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
