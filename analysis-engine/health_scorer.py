import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Path setup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), ".."))))

from backend.app.database import SessionLocal
from backend.app.models import Station, AnomalyFlag, SensorHealthScore, RawReading

def compute_tier_and_recommendation(score: float) -> tuple[str, str]:
    if score >= 85.0:
        tier = "Healthy"
        recommendation = "Sensor operating within normal parameters. Routine scheduled maintenance only."
    elif score >= 70.0:
        tier = "Watch"
        recommendation = "Minor anomalous events detected recently. Monitor station telemetry during upcoming weather changes."
    elif score >= 50.0:
        tier = "Degraded"
        recommendation = "Persistent or recurrent sensor faults detected (e.g. drift/frozen readings). Field inspection and sensor re-calibration recommended."
    else:
        tier = "Critical"
        recommendation = "Severe or continuous sensor failure (e.g. prolonged missing/frozen data). Immediate hardware maintenance or sensor replacement required."
    return tier, recommendation

def calculate_sensor_health_scores():
    print("=" * 65)
    print("  AETHERIX SENTINEL - Phase 3 Sensor Health Scoring Engine")
    print("=" * 65)
    
    db = SessionLocal()
    try:
        stations = db.query(Station).all()
        max_ts = db.query(AnomalyFlag.timestamp).order_by(AnomalyFlag.timestamp.desc()).first()[0]
        cutoff_30d = max_ts - timedelta(days=30)
        
        # Clear existing scores for idempotency
        db.query(SensorHealthScore).delete()
        db.commit()
        
        score_records = []
        
        for st in stations:
            st_id = st.station_id
            st_scores = []
            
            for var in ["temperature", "humidity", "pressure"]:
                # Query 30-day flags for station & variable
                flags = db.query(AnomalyFlag).filter(
                    AnomalyFlag.station_id == st_id,
                    AnomalyFlag.variable == var,
                    AnomalyFlag.timestamp >= cutoff_30d
                ).all()
                
                fault_flags = [f for f in flags if f.predicted_fault_type != "none"]
                fault_count = len(fault_flags)
                
                base_score = 100.0
                
                # 1. Fault Frequency Penalty
                freq_penalty = fault_count * 0.2
                
                # 2. Recency Penalty
                recency_days = 999.0
                recency_penalty = 0.0
                if fault_flags:
                    last_fault_ts = max(f.timestamp for f in fault_flags)
                    recency_days = round((max_ts - last_fault_ts).total_seconds() / 86400.0, 1)
                    if recency_days < 1.0:
                        recency_penalty = 15.0
                    elif recency_days < 3.0:
                        recency_penalty = 10.0
                    elif recency_days < 7.0:
                        recency_penalty = 5.0
                        
                # 3. Severity & Fault Type Breakdown
                severity_penalty = 0.0
                for f in fault_flags:
                    ft = f.predicted_fault_type
                    if ft == "missing":
                        severity_penalty += 0.8
                    elif ft == "frozen":
                        severity_penalty += 0.6
                    elif ft == "drift":
                        severity_penalty += 0.4
                    elif ft == "spike":
                        severity_penalty += 0.2
                        
                # 4. Confidence Trend Adjustment
                normal_flags = [f for f in flags if f.predicted_fault_type == "none"]
                recent_conf = np.mean([f.ml_confidence for f in normal_flags[-50:]]) if normal_flags else 0.9
                conf_bonus = 5.0 if recent_conf > 0.90 else 0.0
                
                final_score = max(0.0, min(100.0, base_score - freq_penalty - recency_penalty - severity_penalty + conf_bonus))
                tier, rec = compute_tier_and_recommendation(final_score)
                
                st_scores.append(final_score)
                
                score_records.append({
                    "station_id": st_id,
                    "variable": var,
                    "health_score": round(float(final_score), 1),
                    "status_tier": tier,
                    "fault_count_30d": fault_count,
                    "recency_days": float(recency_days) if recency_days < 900 else None,
                    "maintenance_recommendation": rec,
                    "last_updated": max_ts
                })
                
            # Overall Station Score
            overall_score = round(float(np.mean(st_scores)), 1)
            overall_tier, overall_rec = compute_tier_and_recommendation(overall_score)
            
            score_records.append({
                "station_id": st_id,
                "variable": "overall",
                "health_score": overall_score,
                "status_tier": overall_tier,
                "fault_count_30d": sum(r["fault_count_30d"] for r in score_records[-3:]),
                "recency_days": min((r["recency_days"] for r in score_records[-3:] if r["recency_days"] is not None), default=None),
                "maintenance_recommendation": overall_rec,
                "last_updated": max_ts
            })
            
        # Insert records into DB
        db.bulk_insert_mappings(SensorHealthScore, score_records)
        db.commit()
        print(f"      Calculated & stored {len(score_records)} health score records across {len(stations)} stations!")
        print("=" * 65 + "\n")
        
        return score_records
        
    finally:
        db.close()

if __name__ == "__main__":
    calculate_sensor_health_scores()
