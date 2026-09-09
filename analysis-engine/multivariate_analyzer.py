import pandas as pd
import numpy as np

def compute_multivariate_consistency(db, station_id, timestamp, primary_variable, primary_score=0.0):
    """
    Computes joint multivariate consistency score across Temp, Humidity, and Pressure
    at the same station and timestamp.
    
    Returns:
      score: float between 0.0 (isolated single-sensor fault) and 1.0 (correlated multi-variable weather event)
      narrative_clause: str explanation of multivariate alignment
    """
    from backend.app.models import RawReading, AnomalyFlag
    
    # Query readings around timestamp (window of +/- 1 hour)
    readings = db.query(RawReading).filter(
        RawReading.station_id == station_id,
        RawReading.timestamp == timestamp
    ).first()
    
    if not readings:
        return 0.1, "Single-variable anomaly; no concurrent telemetry available."
        
    # Query anomaly flags for all 3 variables at this timestamp
    flags = db.query(AnomalyFlag).filter(
        AnomalyFlag.station_id == station_id,
        AnomalyFlag.timestamp == timestamp
    ).all()
    
    flag_dict = {f.variable: f for f in flags}
    
    vars_list = ["temperature", "humidity", "pressure"]
    other_vars = [v for v in vars_list if v != primary_variable]
    
    # Check concurrent activity in other variables
    other_scores = []
    for v in other_vars:
        flg = flag_dict.get(v)
        if flg:
            # Maximum of temporal/spatial/drift score
            score = max(flg.temporal_score, flg.spatial_score, getattr(flg, "drift_score", 0.0))
            other_scores.append(score)
        else:
            other_scores.append(0.0)
            
    avg_other_score = float(np.mean(other_scores)) if other_scores else 0.0
    
    # Calculate multivariate correlation score:
    # If primary variable score is high, but other variables are 0, score is LOW (<0.3) -> isolated sensor fault.
    # If other variables also show correlated shifts, score is HIGH (>0.7) -> regional synoptic event.
    if avg_other_score > 1.5:
        consistency_score = min(0.95, round(0.70 + (avg_other_score / 10.0), 2))
        clause = f"Multi-variable correlated shift detected across {', '.join(other_vars)} (consistency score: {consistency_score*100:.0f}%), indicating a synoptic regional weather pattern."
    else:
        consistency_score = max(0.08, round(0.15 - (primary_score / 20.0), 2))
        clause = f"{primary_variable.capitalize()} anomaly occurred in isolation without correlated shifts in {', '.join(other_vars)} (multivariate consistency score: {consistency_score*100:.0f}%), strongly indicating a single-sensor hardware fault."
        
    return consistency_score, clause
