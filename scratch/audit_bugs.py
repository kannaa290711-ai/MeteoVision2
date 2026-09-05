import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from backend.app.database import SessionLocal
from backend.app.models import AnomalyFlag, ImputedReading, XAINarrative, Station, GroundTruthFault

def audit():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("  AUDITING BUG 1: DRIFT ANOMALY FLAGS & NEIGHBOR AGREEMENT")
        print("=" * 60)
        
        # Look at AWS-001 temperature drift flags
        drift_flags = db.query(AnomalyFlag).filter(
            AnomalyFlag.predicted_fault_type == "drift"
        ).limit(10).all()
        
        for f in drift_flags:
            print(f"Flag ID={f.id} | Station={f.station_id} | Var={f.variable} | TS={f.timestamp}")
            print(f"  Scores: Temp={f.temporal_score:.2f}, Spatial={f.spatial_score:.2f}, Drift={f.drift_score:.2f}, Frozen={f.frozen_score:.2f}")
            print(f"  Neighbor Agreement={f.neighbor_agreement*100:.1f}% | ML Conf={f.ml_confidence*100:.1f}%")
            
            # Check ground truth label for this point
            gt = db.query(GroundTruthFault).filter(
                GroundTruthFault.station_id == f.station_id,
                GroundTruthFault.variable == f.variable,
                GroundTruthFault.start_time <= f.timestamp,
                GroundTruthFault.end_time >= f.timestamp
            ).first()
            print(f"  Ground Truth: {gt.fault_type if gt else 'NONE (Normal/Weather Event)'}")
            print("-" * 50)
            
        print("\n" + "=" * 60)
        print("  AUDITING BUG 2: MISSING VALUE IMPUTATION CONFIDENCE")
        print("=" * 60)
        
        missing_imps = db.query(ImputedReading, AnomalyFlag).join(
            AnomalyFlag, ImputedReading.flag_id == AnomalyFlag.id
        ).filter(
            AnomalyFlag.predicted_fault_type == "missing"
        ).limit(5).all()
        
        for imp, f in missing_imps:
            print(f"Imputed ID={imp.id} | Station={imp.station_id} | Var={imp.variable} | TS={imp.timestamp}")
            print(f"  Estimated={imp.estimated_value} | Spatial={imp.spatial_estimate} | Temporal={imp.temporal_estimate}")
            print(f"  Method={imp.imputation_method} | Imputed Conf={imp.imputation_confidence*100:.1f}% | ML Conf={f.ml_confidence*100:.1f}%")
            print("-" * 50)

    finally:
        db.close()

if __name__ == "__main__":
    audit()
