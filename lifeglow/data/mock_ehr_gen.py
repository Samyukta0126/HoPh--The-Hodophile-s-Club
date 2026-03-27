"""
LifeGLOW Mock EHR Data Generator
Generates FHIR R4 AuditEvent-compliant CSV for 100 nurses over 30 days
Distribution: ~40% Low, ~30% Medium, ~20% High, ~10% Critical risk

Output: mock_ehr_data.csv with realistic variation for dashboard testing
"""

import csv
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


# Configuration
NUM_NURSES = 100
NUM_DAYS = 30
START_DATE = datetime(2025, 1, 1)

# Hospital units
UNITS = ['ICU', '4B', 'ED', 'PEDS', 'ONC', 'NICU', 'OR', 'PACU']

# Risk distribution targets
RISK_DISTRIBUTION = {
    'Low': 0.40,      # 40 nurses
    'Medium': 0.30,   # 30 nurses
    'High': 0.20,     # 20 nurses
    'Critical': 0.10  # 10 nurses
}


def generate_nurse_profiles() -> List[Dict[str, Any]]:
    """Generate 100 nurse profiles with assigned risk levels"""
    nurses = []
    
    # Calculate exact counts per risk level
    risk_counts = {
        'Low': int(NUM_NURSES * RISK_DISTRIBUTION['Low']),
        'Medium': int(NUM_NURSES * RISK_DISTRIBUTION['Medium']),
        'High': int(NUM_NURSES * RISK_DISTRIBUTION['High']),
        'Critical': NUM_NURSES - int(NUM_NURSES * (
            RISK_DISTRIBUTION['Low'] + 
            RISK_DISTRIBUTION['Medium'] + 
            RISK_DISTRIBUTION['High']
        ))  # Remainder to Critical
    }
    
    # Create risk level assignments
    risk_assignments = []
    for risk_level, count in risk_counts.items():
        risk_assignments.extend([risk_level] * count)
    
    # Shuffle to randomize assignment
    random.shuffle(risk_assignments)
    
    for i in range(NUM_NURSES):
        nurse_id = str(uuid.uuid4())
        unit = random.choice(UNITS)
        risk_level = risk_assignments[i]
        
        nurses.append({
            'nurse_id': nurse_id,
            'unit_id': unit,
            'risk_profile': risk_level
        })
    
    return nurses


def generate_shift_data(nurse: Dict[str, Any], day: int) -> Dict[str, Any]:
    """
    Generate shift data for a nurse on a specific day based on risk profile
    
    Risk profiles influence:
    - Pajama Time (notes filed after shift)
    - Shift Overrun (clock-out time)
    - Recovery Debt (consecutive shifts, rest time)
    - PTO Stagnation (time off taken)
    """
    risk_profile = nurse['risk_profile']
    base_date = START_DATE + timedelta(days=day)
    
    # Shift schedule (12-hour shifts typical)
    shift_start = base_date.replace(hour=7, minute=0, second=0)
    shift_end = base_date.replace(hour=19, minute=30, second=0)
    
    # Adjust behavior based on risk profile
    if risk_profile == 'Low':
        # Healthy patterns
        clock_out_delay = random.randint(-5, 15)  # Usually on time or slightly late
        note_filing_delay = random.uniform(0, 1.5)  # Notes filed during or right after shift
        consecutive_shifts = random.choice([1, 2, 1, 1, 2])  # Mostly 1-2 shifts
        hours_rest = random.uniform(12, 16)
        pto_days_60d = random.randint(2, 5)
        break_taken = random.random() > 0.1  # 90% take breaks
        
    elif risk_profile == 'Medium':
        # Emerging stress patterns
        clock_out_delay = random.randint(10, 40)
        note_filing_delay = random.uniform(1.5, 3.0)
        consecutive_shifts = random.choice([2, 3, 2, 3, 3])
        hours_rest = random.uniform(10, 13)
        pto_days_60d = random.randint(1, 2)
        break_taken = random.random() > 0.25  # 75% take breaks
        
    elif risk_profile == 'High':
        # Significant stress patterns
        clock_out_delay = random.randint(35, 70)
        note_filing_delay = random.uniform(2.5, 5.0)
        consecutive_shifts = random.choice([3, 4, 4, 5, 3])
        hours_rest = random.uniform(8, 11)
        pto_days_60d = random.randint(0, 1)
        break_taken = random.random() > 0.4  # 60% take breaks
        
    else:  # Critical
        # Crisis patterns
        clock_out_delay = random.randint(60, 120)
        note_filing_delay = random.uniform(4.0, 8.0)
        consecutive_shifts = random.choice([4, 5, 5, 6, 6, 7])
        hours_rest = random.uniform(6, 9)
        pto_days_60d = 0
        break_taken = random.random() > 0.5  # 50% take breaks
    
    # Calculate actual times
    clock_out_actual = shift_end + timedelta(minutes=clock_out_delay)
    note_filed_time = shift_end + timedelta(hours=note_filing_delay)
    
    # Sometimes notes are filed during shift (reduce delay)
    if random.random() > 0.3:
        note_filed_time = shift_start + timedelta(
            hours=random.uniform(4, 8),
            minutes=random.randint(0, 59)
        )
    
    # Some days off (no shift data)
    has_shift = True
    if risk_profile in ['Low', 'Medium'] and day % 7 == 6:  # Regular weekends off
        has_shift = random.random() > 0.2
    elif risk_profile in ['High', 'Critical']:
        has_shift = random.random() > 0.05  # Rarely off
    
    return {
        'nurse_id': nurse['nurse_id'],
        'unit_id': nurse['unit_id'],
        'shift_start': shift_start.isoformat() if has_shift else '',
        'shift_end': shift_end.isoformat() if has_shift else '',
        'clock_out_actual': clock_out_actual.isoformat() if has_shift and clock_out_delay > 0 else '',
        'note_filed_time': note_filed_time.isoformat() if has_shift else '',
        'pto_days_taken': pto_days_60d,
        'consecutive_shifts': consecutive_shifts if has_shift else 0,
        'break_taken': str(break_taken).lower() if has_shift else '',
        'has_shift': has_shift
    }


def calculate_risk_metrics(shift_records: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate aggregate risk metrics from shift records
    Used to validate distribution matches targets
    """
    if not shift_records:
        return {}
    
    # Average note filing delay after shift end
    note_delays = []
    overrun_minutes = []
    consecutive_shifts_list = []
    pto_days_list = []
    
    for record in shift_records:
        if not record.get('shift_end') or not record.get('note_filed_time'):
            continue
            
        try:
            shift_end = datetime.fromisoformat(record['shift_end'])
            note_time = datetime.fromisoformat(record['note_filed_time'])
            
            # Hours between shift end and note filing
            delay_hours = (note_time - shift_end).total_seconds() / 3600
            if delay_hours > 0:
                note_delays.append(delay_hours)
                
            # Clock-out overrun
            if record.get('clock_out_actual'):
                clock_out = datetime.fromisoformat(record['clock_out_actual'])
                overrun = (clock_out - shift_end).total_seconds() / 60
                if overrun > 0:
                    overrun_minutes.append(overrun)
                    
            # Consecutive shifts
            if record.get('consecutive_shifts'):
                consecutive_shifts_list.append(record['consecutive_shifts'])
                
            # PTO days
            if record.get('pto_days_taken') is not None:
                pto_days_list.append(record['pto_days_taken'])
                
        except (ValueError, TypeError):
            continue
    
    return {
        'avg_note_delay_hours': sum(note_delays) / len(note_delays) if note_delays else 0,
        'avg_overrun_minutes': sum(overrun_minutes) / len(overrun_minutes) if overrun_minutes else 0,
        'avg_consecutive_shifts': sum(consecutive_shifts_list) / len(consecutive_shifts_list) if consecutive_shifts_list else 0,
        'avg_pto_days': sum(pto_days_list) / len(pto_days_list) if pto_days_list else 0
    }


def generate_mock_ehr_data(output_file: str = 'mock_ehr_data.csv'):
    """
    Main function to generate complete mock EHR dataset
    
    Generates 100 nurses × 30 days of shift data
    Outputs FHIR R4 AuditEvent-compliant CSV
    """
    print(f"Generating mock EHR data for {NUM_NURSES} nurses over {NUM_DAYS} days...")
    
    # Generate nurse profiles with risk distribution
    nurses = generate_nurse_profiles()
    
    # Count by risk profile for validation
    risk_counts = {}
    for nurse in nurses:
        risk = nurse['risk_profile']
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    print(f"Nurse distribution: {risk_counts}")
    
    # Generate shift records
    all_records = []
    
    for nurse in nurses:
        for day in range(NUM_DAYS):
            shift_data = generate_shift_data(nurse, day)
            
            # Only include records with actual shifts
            if shift_data['has_shift']:
                # Remove the helper field before adding to output
                del shift_data['has_shift']
                all_records.append(shift_data)
    
    # Write to CSV
    fieldnames = [
        'nurse_id',
        'unit_id',
        'shift_start',
        'shift_end',
        'clock_out_actual',
        'note_filed_time',
        'pto_days_taken',
        'consecutive_shifts',
        'break_taken'
    ]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"Generated {len(all_records)} shift records to {output_file}")
    
    # Validate distribution by sampling
    print("\nValidating risk distribution...")
    
    # Group records by nurse for metric calculation
    nurse_records = {}
    for record in all_records:
        nid = record['nurse_id']
        if nid not in nurse_records:
            nurse_records[nid] = []
        nurse_records[nid].append(record)
    
    # Sample metrics from first 10 nurses per risk level
    sample_metrics = {}
    for nurse in nurses[:40]:  # Sample first 40
        risk = nurse['risk_profile']
        if risk not in sample_metrics:
            sample_metrics[risk] = []
        
        metrics = calculate_risk_metrics(nurse_records[nurse['nurse_id']])
        if metrics:
            sample_metrics[risk].append(metrics)
    
    # Print sample statistics
    for risk, metrics_list in sample_metrics.items():
        if metrics_list:
            avg_note_delay = sum(m['avg_note_delay_hours'] for m in metrics_list) / len(metrics_list)
            avg_overrun = sum(m['avg_overrun_minutes'] for m in metrics_list) / len(metrics_list)
            print(f"  {risk}: Avg note delay={avg_note_delay:.2f}h, Avg overrun={avg_overrun:.1f}min")
    
    print(f"\n✓ Data generation complete!")
    print(f"  Total records: {len(all_records)}")
    print(f"  Date range: {START_DATE.date()} to {(START_DATE + timedelta(days=NUM_DAYS-1)).date()}")
    print(f"  Units covered: {', '.join(UNITS)}")
    
    return output_file


if __name__ == "__main__":
    import os
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Generate data
    output_path = generate_mock_ehr_data('data/mock_ehr_data.csv')
    
    # Verify file exists
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"\nFile size: {file_size:,} bytes")
        
        # Show first few lines
        print("\nSample data (first 5 rows):")
        with open(output_path, 'r') as f:
            for i, line in enumerate(f):
                if i < 6:
                    print(line.strip())
