import os
import sys
import joblib
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../analysis-engine")))

from backend.app.database import SessionLocal
from backend.app.models import AnomalyFlag, RawReading, Station, XAINarrative
from shap_explainer import compute_shap_breakdown

db = SessionLocal()
try:
    # Query diverse flagged anomalies
    flags = db.query(AnomalyFlag, Station.name, Station.elevation_m).join(
        Station, AnomalyFlag.station_id == Station.station_id
    ).filter(
        AnomalyFlag.flagged == True,
        AnomalyFlag.predicted_fault_type.in_(["spike", "frozen", "drift", "missing"])
    ).order_by(AnomalyFlag.id.asc()).limit(30).all()
    
    print("=" * 80)
    print("PART 4 — SPOT-CHECKING SHAP ATTRIBUTIONS VS DETERMINISTIC NARRATIVES")
    print("=" * 80)
    
    for idx, (flag, st_name, elev_m) in enumerate(flags[:10]):
        xai = db.query(XAINarrative).filter(XAINarrative.flag_id == flag.id).first()
        narrative_text = xai.explanation_text if xai else "N/A"
        
        feature_dict = {
            "temporal_score": float(flag.temporal_score),
            "spatial_score": float(flag.spatial_score),
            "frozen_score": float(getattr(flag, "frozen_score", 0.0)),
            "drift_score": float(getattr(flag, "drift_score", 0.0)),
            "neighbor_agreement": float(getattr(flag, "neighbor_agreement", 1.0)),
            "hour_of_day": int(flag.timestamp.hour),
            "elevation_m": float(elev_m or 500.0)
        }
        
        shap_res = compute_shap_breakdown(feature_dict)
        
        print(f"\n--- [Example {idx+1}] Flag ID #{flag.id} | Fault: {flag.predicted_fault_type.upper()} | Station: {flag.station_id} ({st_name}) ---")
        print(f"Feature Values : TempScore={flag.temporal_score:.2f}, SpatialScore={flag.spatial_score:.2f}, FrozenScore={getattr(flag, 'frozen_score', 0.0):.2f}, DriftScore={getattr(flag, 'drift_score', 0.0):.2f}")
        print(f"XAI Narrative  : {narrative_text[:140]}...")
        print(f"SHAP Summary   : {shap_res['top_drivers']}")
        print(f"SHAP Full Pcts : {shap_res['feature_contributions']}")

finally:
    db.close()
