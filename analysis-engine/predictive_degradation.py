import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, AnomalyFlag, SensorHealthScore

def compute_predictive_degradation(station_id: str, db=None):
    """
    Computes Remaining Useful Life (RUL in days) and forecasted health scores (+7d, +14d, +30d)
    for a given AWS station based on historical fault frequency and health score trends.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        # Fetch current health scores for the station
        scores = db.query(SensorHealthScore).filter(
            SensorHealthScore.station_id == station_id
        ).all()
        
        if not scores:
            # Fallback if health scores haven't been computed yet
            scores_dict = {
                "overall": {"score": 95.0, "faults": 0, "tier": "Healthy"},
                "temperature": {"score": 95.0, "faults": 0, "tier": "Healthy"},
                "humidity": {"score": 95.0, "faults": 0, "tier": "Healthy"},
                "pressure": {"score": 95.0, "faults": 0, "tier": "Healthy"}
            }
        else:
            scores_dict = {
                s.variable: {
                    "score": float(s.health_score),
                    "faults": s.fault_count_30d,
                    "tier": s.status_tier,
                    "recency_days": s.recency_days
                } for s in scores
            }

        var_forecasts = {}
        overall_rul_list = []

        for var in ["temperature", "humidity", "pressure", "overall"]:
            st_data = scores_dict.get(var, {"score": 95.0, "faults": 0, "tier": "Healthy"})
            curr_score = st_data["score"]
            faults_30d = st_data.get("faults", 0)
            recency = st_data.get("recency_days")
            
            # Compute daily health decay rate (% per day) based on fault accumulation
            # Base decay rate from fault frequency
            decay_rate_per_day = (faults_30d * 0.08)
            
            # Recency multiplier if a fault occurred in the past 3 days
            if recency is not None and recency < 3.0:
                decay_rate_per_day += (0.5 / max(recency, 0.1))
            
            # Minimum background degradation rate for realistic sensor aging (0.05% per day)
            decay_rate_per_day = max(0.05, min(3.0, decay_rate_per_day))
            
            # Forecast future health scores
            score_7d = round(max(0.0, min(100.0, curr_score - (7 * decay_rate_per_day))), 1)
            score_14d = round(max(0.0, min(100.0, curr_score - (14 * decay_rate_per_day))), 1)
            score_30d = round(max(0.0, min(100.0, curr_score - (30 * decay_rate_per_day))), 1)
            
            # Calculate Remaining Useful Life (RUL) in days until Critical Threshold (< 50.0)
            critical_threshold = 50.0
            if curr_score <= critical_threshold:
                rul_days = 0
            else:
                rul_days = int((curr_score - critical_threshold) / decay_rate_per_day)
                rul_days = min(365, max(0, rul_days))
                
            if var != "overall":
                overall_rul_list.append(rul_days)

            # Risk level assessment
            if rul_days < 7 or curr_score < 50.0:
                risk_level = "CRITICAL"
                advisory = "Immediate maintenance dispatch recommended before complete sensor lockup."
            elif rul_days < 14 or curr_score < 70.0:
                risk_level = "ELEVATED"
                advisory = "Sensor degradation accelerating. Schedule recalibration within 7-10 days."
            elif rul_days < 30:
                risk_level = "MODERATE"
                advisory = "Moderate wear detected. Monitor trend during upcoming weather shifts."
            else:
                risk_level = "LOW"
                advisory = "Sensor operating within nominal health parameters. Normal maintenance cycle."

            var_forecasts[var] = {
                "current_health_score": curr_score,
                "current_tier": st_data["tier"],
                "decay_rate_pct_per_day": round(float(decay_rate_per_day), 2),
                "rul_days": rul_days,
                "risk_level": risk_level,
                "forecast_7d": score_7d,
                "forecast_14d": score_14d,
                "forecast_30d": score_30d,
                "proactive_advisory": advisory
            }

        # Overall station RUL (minimum across variables)
        min_rul = min(overall_rul_list) if overall_rul_list else 180

        return {
            "station_id": station_id,
            "overall_rul_days": min_rul,
            "overall_degradation_risk": var_forecasts.get("overall", {}).get("risk_level", "LOW"),
            "variables": var_forecasts
        }
        
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    res = compute_predictive_degradation("AWS-001")
    print("Predictive Degradation Result for AWS-001:")
    print(res)
