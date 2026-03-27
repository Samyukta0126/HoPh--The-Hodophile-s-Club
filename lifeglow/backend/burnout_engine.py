"""
LifeGLOW Burnout Engine Logic
Rule-based weighted scoring algorithm with Logistic Regression refinement
Produces risk score 0-100 with risk level classification

Compliant with HIPAA Safe Mode - no individual data exposure unless Critical (>85)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import math


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class WorkerData:
    """Input data structure for burnout calculation"""
    worker_id: str
    unit_id: str
    
    # Pajama Time: Clinical notes filed after shift end
    notes_filed_after_shift_hours: float = 0.0  # Hours after shift end
    
    # Shift Overrun: Clock-out time vs scheduled end
    shift_overrun_minutes: float = 0.0  # Minutes past scheduled end
    consecutive_overruns: int = 0  # Number of consecutive days with overrun
    
    # Recovery Debt: Consecutive shifts and rest time
    consecutive_shifts: int = 1
    hours_since_last_shift: float = 24.0
    
    # PTO Stagnation: Time off taken
    pto_days_taken_60d: int = 0
    days_since_last_pto: int = 0
    
    # Historical data for logistic regression
    previous_score: Optional[float] = None


@dataclass
class BurnoutResult:
    """Output structure from burnout calculation"""
    risk_score: int  # 0-100
    risk_level: RiskLevel
    primary_trigger: str
    recommended_action: str
    
    # Component scores for debugging/transparency
    pajama_time_score: float = 0.0
    shift_overrun_score: float = 0.0
    recovery_debt_score: float = 0.0
    pto_stagnation_score: float = 0.0


# Signal weights as specified in requirements
SIGNAL_WEIGHTS = {
    'pajama_time': 0.30,      # 2.43x higher exhaustion risk
    'shift_overrun': 0.30,    # Strongest turnover predictor
    'recovery_debt': 0.25,    # High physiological stress
    'pto_stagnation': 0.15    # Significant early-tenure turnover
}

# Risk level thresholds
RISK_THRESHOLDS = {
    RiskLevel.LOW: (0, 39),
    RiskLevel.MEDIUM: (40, 64),
    RiskLevel.HIGH: (65, 84),
    RiskLevel.CRITICAL: (85, 100)
}


def _calculate_pajama_time_score(hours_after_shift: float) -> float:
    """
    Calculate pajama time component score (0-100 scale)
    
    Trigger: Clinical notes filed >2 hrs after shift end
    Impact: 2.43x higher exhaustion risk
    
    Scoring:
    - 0-2 hours: 0 points (normal)
    - 2-4 hours: 25-50 points
    - 4-6 hours: 50-75 points
    - >6 hours: 75-100 points (severe)
    """
    if hours_after_shift <= 2.0:
        return 0.0
    
    # Logarithmic scaling for severity
    if hours_after_shift <= 4.0:
        return min(50.0, (hours_after_shift - 2.0) * 25.0)
    elif hours_after_shift <= 6.0:
        return min(75.0, 50.0 + (hours_after_shift - 4.0) * 12.5)
    else:
        return min(100.0, 75.0 + (hours_after_shift - 6.0) * 5.0)


def _calculate_shift_overrun_score(overrun_minutes: float, consecutive_days: int) -> float:
    """
    Calculate shift overrun component score (0-100 scale)
    
    Trigger: Clock-out >45 mins past shift end, consistently
    Impact: Strongest turnover predictor
    
    Scoring considers both magnitude and consistency:
    - Single occurrence <45 mins: 0 points
    - Single occurrence >45 mins: 20-40 points
    - Consistent (>3 days): 40-100 points based on severity
    """
    if overrun_minutes <= 15:
        base_score = 0.0
    elif overrun_minutes <= 45:
        base_score = 20.0 + (overrun_minutes - 15) * 0.5
    else:
        base_score = 40.0 + min(40.0, (overrun_minutes - 45) * 0.5)
    
    # Multiplier for consecutive occurrences
    consistency_multiplier = 1.0
    if consecutive_days >= 3:
        consistency_multiplier = 1.5 + (consecutive_days - 3) * 0.2
    elif consecutive_days >= 1:
        consistency_multiplier = 1.0 + consecutive_days * 0.15
    
    return min(100.0, base_score * consistency_multiplier)


def _calculate_recovery_debt_score(consecutive_shifts: int, hours_rest: float) -> float:
    """
    Calculate recovery debt component score (0-100 scale)
    
    Trigger: 3+ consecutive shifts OR <10 hrs between shifts
    Impact: High physiological stress
    
    Scoring:
    - 1-2 shifts with adequate rest: 0 points
    - 3-4 shifts or marginal rest: 25-50 points
    - 5+ shifts or insufficient rest: 50-100 points
    """
    shift_score = 0.0
    if consecutive_shifts >= 5:
        shift_score = 75.0 + min(25.0, (consecutive_shifts - 5) * 5.0)
    elif consecutive_shifts >= 3:
        shift_score = 25.0 + (consecutive_shifts - 3) * 25.0
    else:
        shift_score = max(0.0, (2 - consecutive_shifts) * 10.0)
    
    rest_score = 0.0
    if hours_rest < 8.0:
        rest_score = 80.0 + (8.0 - hours_rest) * 5.0
    elif hours_rest < 10.0:
        rest_score = 30.0 + (10.0 - hours_rest) * 15.0
    elif hours_rest < 12.0:
        rest_score = 10.0 + (12.0 - hours_rest) * 5.0
    
    # Take the worse of the two factors
    return min(100.0, max(shift_score, rest_score))


def _calculate_pto_stagnation_score(pto_days_60d: int, days_since_pto: int) -> float:
    """
    Calculate PTO stagnation component score (0-100 scale)
    
    Trigger: Zero PTO days taken in 60 days
    Impact: Significant early-tenure turnover
    
    Scoring:
    - 2+ days in 60d: 0 points (healthy)
    - 1 day in 60d: 25 points
    - 0 days in 60d: 50-100 points based on time since last PTO
    """
    if pto_days_60d >= 2:
        return 0.0
    elif pto_days_60d == 1:
        return 25.0
    else:
        # No PTO in 60 days - severity increases with time
        if days_since_pto <= 60:
            return 50.0
        elif days_since_pto <= 90:
            return 50.0 + (days_since_pto - 60) * 1.0
        else:
            return min(100.0, 80.0 + (days_since_pto - 90) * 0.5)


def _logistic_regression_adjustment(
    raw_score: float,
    worker_data: WorkerData
) -> float:
    """
    Apply logistic regression refinement to raw score
    
    Uses historical patterns to adjust score based on:
    - Previous burnout score (if available)
    - Rate of change in indicators
    - Combined effect of multiple triggers
    
    Logistic function: adjusted = 100 / (1 + e^(-k*(raw_score - midpoint)))
    """
    # Base logistic curve parameters
    k = 0.08  # Steepness
    midpoint = 50.0  # Inflection point
    
    # Apply logistic transformation
    logistic_adjusted = 100.0 / (1.0 + math.exp(-k * (raw_score - midpoint)))
    
    # Historical trend adjustment
    if worker_data.previous_score is not None:
        trend = raw_score - worker_data.previous_score
        
        # Accelerating burnout (positive trend) gets additional weight
        if trend > 10:
            logistic_adjusted = min(100.0, logistic_adjusted + 5.0)
        elif trend > 5:
            logistic_adjusted = min(100.0, logistic_adjusted + 2.5)
        # Improving trend gets slight reduction
        elif trend < -10:
            logistic_adjusted = max(0.0, logistic_adjusted - 5.0)
        elif trend < -5:
            logistic_adjusted = max(0.0, logistic_adjusted - 2.5)
    
    # Multi-trigger amplification
    active_triggers = sum([
        1 if worker_data.notes_filed_after_shift_hours > 2 else 0,
        1 if worker_data.shift_overrun_minutes > 45 else 0,
        1 if worker_data.consecutive_shifts >= 3 or worker_data.hours_since_last_shift < 10 else 0,
        1 if worker_data.pto_days_taken_60d == 0 else 0
    ])
    
    if active_triggers >= 3:
        logistic_adjusted = min(100.0, logistic_adjusted + 8.0)
    elif active_triggers >= 2:
        logistic_adjusted = min(100.0, logistic_adjusted + 4.0)
    
    return logistic_adjusted


def _determine_risk_level(score: int) -> RiskLevel:
    """Determine risk level based on score thresholds"""
    for level, (min_score, max_score) in RISK_THRESHOLDS.items():
        if min_score <= score <= max_score:
            return level
    return RiskLevel.CRITICAL if score > 100 else RiskLevel.LOW


def _generate_recommendation(
    primary_trigger: str,
    risk_level: RiskLevel,
    worker_data: WorkerData
) -> str:
    """Generate prescriptive nudge text for manager"""
    
    recommendations = {
        'Pajama Time': (
            f"Staff documenting clinical notes {worker_data.notes_filed_after_shift_hours:.1f}hrs "
            f"after shift end. Consider: workflow optimization, documentation support, "
            f"or workload redistribution."
        ),
        'Shift Overrun': (
            f"Consistent shift overruns detected ({worker_data.shift_overrun_minutes:.0f}min avg). "
            f"Recommend: review staffing levels, assess patient acuity, consider float nurse support."
        ),
        'Recovery Debt': (
            f"{worker_data.consecutive_shifts} consecutive shifts with only "
            f"{worker_data.hours_since_last_shift:.1f}hrs rest. Immediate action required: "
            f"mandate rest period, adjust upcoming schedule."
        ),
        'PTO Stagnation': (
            f"No PTO taken in 60+ days. Recommend: proactive time-off scheduling, "
            f"wellness check-in, peer support activation."
        )
    }
    
    base_recommendation = recommendations.get(
        primary_trigger,
        "Monitor closely and consider wellness check-in."
    )
    
    # Add urgency modifier based on risk level
    urgency_prefix = {
        RiskLevel.CRITICAL: "[CRITICAL] ",
        RiskLevel.HIGH: "[HIGH PRIORITY] ",
        RiskLevel.MEDIUM: "[MODERATE] ",
        RiskLevel.LOW: "[MONITOR] "
    }
    
    return urgency_prefix[risk_level] + base_recommendation


def calculate_burnout_risk(worker_data: WorkerData) -> BurnoutResult:
    """
    Main burnout risk calculation function
    
    Applies weighted scoring algorithm with logistic regression refinement
    Returns score 0-100 with risk level and actionable recommendation
    
    Args:
        worker_data: WorkerData object with shift/EHR metrics
        
    Returns:
        BurnoutResult with score, level, trigger, and recommendation
    """
    # Calculate component scores
    pajama_score = _calculate_pajama_time_score(
        worker_data.notes_filed_after_shift_hours
    )
    
    overrun_score = _calculate_shift_overrun_score(
        worker_data.shift_overrun_minutes,
        worker_data.consecutive_overruns
    )
    
    recovery_score = _calculate_recovery_debt_score(
        worker_data.consecutive_shifts,
        worker_data.hours_since_last_shift
    )
    
    pto_score = _calculate_pto_stagnation_score(
        worker_data.pto_days_taken_60d,
        worker_data.days_since_last_pto
    )
    
    # Apply weights to component scores
    weighted_score = (
        pajama_score * SIGNAL_WEIGHTS['pajama_time'] +
        overrun_score * SIGNAL_WEIGHTS['shift_overrun'] +
        recovery_score * SIGNAL_WEIGHTS['recovery_debt'] +
        pto_score * SIGNAL_WEIGHTS['pto_stagnation']
    )
    
    # Apply logistic regression refinement
    final_score = _logistic_regression_adjustment(weighted_score, worker_data)
    
    # Round to integer and clamp to 0-100
    risk_score = max(0, min(100, round(final_score)))
    
    # Determine risk level
    risk_level = _determine_risk_level(risk_score)
    
    # Identify primary trigger (highest weighted component)
    component_scores = {
        'Pajama Time': pajama_score * SIGNAL_WEIGHTS['pajama_time'],
        'Shift Overrun': overrun_score * SIGNAL_WEIGHTS['shift_overrun'],
        'Recovery Debt': recovery_score * SIGNAL_WEIGHTS['recovery_debt'],
        'PTO Stagnation': pto_score * SIGNAL_WEIGHTS['pto_stagnation']
    }
    
    primary_trigger = max(component_scores, key=component_scores.get)
    
    # Generate recommendation
    recommended_action = _generate_recommendation(
        primary_trigger,
        risk_level,
        worker_data
    )
    
    return BurnoutResult(
        risk_score=risk_score,
        risk_level=risk_level,
        primary_trigger=primary_trigger,
        recommended_action=recommended_action,
        pajama_time_score=pajama_score,
        shift_overrun_score=overrun_score,
        recovery_debt_score=recovery_score,
        pto_stagnation_score=pto_score
    )


def calculate_unit_aggregate_risk(
    worker_results: list[BurnoutResult],
    unit_id: str,
    min_k_anonymity: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Calculate aggregated unit-level risk score
    
    Enforces k-anonymity (minimum workers required)
    Returns None if insufficient data for privacy compliance
    
    Args:
        worker_results: List of individual BurnoutResult objects
        unit_id: Hospital unit identifier
        min_k_anonymity: Minimum number of workers (default 5)
        
    Returns:
        Dictionary with aggregated metrics or None if k < min_k_anonymity
    """
    if len(worker_results) < min_k_anonymity:
        return None  # Privacy protection - insufficient data
    
    scores = [r.risk_score for r in worker_results]
    
    return {
        'unit_id': unit_id,
        'worker_count': len(worker_results),
        'avg_score': round(sum(scores) / len(scores), 2),
        'min_score': min(scores),
        'max_score': max(scores),
        'risk_distribution': {
            'Low': sum(1 for r in worker_results if r.risk_level == RiskLevel.LOW),
            'Medium': sum(1 for r in worker_results if r.risk_level == RiskLevel.MEDIUM),
            'High': sum(1 for r in worker_results if r.risk_level == RiskLevel.HIGH),
            'Critical': sum(1 for r in worker_results if r.risk_level == RiskLevel.CRITICAL)
        },
        'common_triggers': list(set(r.primary_trigger for r in worker_results)),
        'requires_intervention': any(r.risk_level == RiskLevel.CRITICAL for r in worker_results)
    }


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: Low risk worker
    low_risk_worker = WorkerData(
        worker_id="test-001",
        unit_id="ICU",
        notes_filed_after_shift_hours=0.5,
        shift_overrun_minutes=10,
        consecutive_overruns=0,
        consecutive_shifts=2,
        hours_since_last_shift=14,
        pto_days_taken_60d=3,
        days_since_last_pto=15
    )
    
    result_low = calculate_burnout_risk(low_risk_worker)
    print(f"Low Risk Test: Score={result_low.risk_score}, Level={result_low.risk_level.value}")
    print(f"  Primary Trigger: {result_low.primary_trigger}")
    print(f"  Recommendation: {result_low.recommended_action}\n")
    
    # Test case 2: Critical risk worker
    critical_worker = WorkerData(
        worker_id="test-002",
        unit_id="ED",
        notes_filed_after_shift_hours=4.5,
        shift_overrun_minutes=90,
        consecutive_overruns=5,
        consecutive_shifts=6,
        hours_since_last_shift=7,
        pto_days_taken_60d=0,
        days_since_last_pto=75,
        previous_score=65.0
    )
    
    result_critical = calculate_burnout_risk(critical_worker)
    print(f"Critical Risk Test: Score={result_critical.risk_score}, Level={result_critical.risk_level.value}")
    print(f"  Primary Trigger: {result_critical.primary_trigger}")
    print(f"  Recommendation: {result_critical.recommended_action}\n")
    
    # Test aggregation with k-anonymity
    test_results = [result_low, result_critical]
    aggregate = calculate_unit_aggregate_risk(test_results, "ICU", min_k_anonymity=5)
    
    if aggregate is None:
        print("Aggregation blocked: Insufficient workers for k-anonymity (k<5)")
    else:
        print(f"Unit Aggregate: {aggregate}")
