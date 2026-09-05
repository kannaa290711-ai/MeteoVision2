import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from backend.app.database import SessionLocal
from backend.app.crud import (
    get_all_stations_with_status, get_station_history, get_recent_alerts,
    get_data_lineage, get_sensor_health_details
)
from backend.app.models import ImputedReading, SensorHealthScore, XAINarrative, AnomalyFlag, Station, RawReading

def generate_report_samples():
    db = SessionLocal()
    try:
        print("============================================================")
        print("  AETHERIX SENTINEL - Phase 3 Deliverable Samples Audit")
        print("============================================================")

        # 1. Sample of 3-5 Self-Healed Readings
        print("\n--- 1. Self-Healed Imputed Readings Sample ---")
        imputed = db.query(ImputedReading).limit(5).all()
        for idx, imp in enumerate(imputed, 1):
            print(f"Sample #{idx}:")
            print(f"  Station / Var / TS : {imp.station_id} | {imp.variable} | {imp.timestamp}")
            print(f"  Raw Value          : {imp.raw_value}")
            print(f"  Estimated Value    : {imp.estimated_value}")
            print(f"  Method Used        : {imp.imputation_method}")
            print(f"  Spatial / Temporal : {imp.spatial_estimate} / {imp.temporal_estimate}")
            print(f"  Imputation Conf.   : {imp.imputation_confidence*100:.1f}%")
            print(f"  Physics Check      : {'PASSED' if imp.physics_check_passed else 'FAILED'} ({imp.physics_check_details})")
            print(f"  Status Label       : '{imp.status_label}'")
            print("-" * 50)

        # 2. Sensor Health Scores for 2-3 Stations
        print("\n--- 2. Sensor Health Score Examples ---")
        for st_id in ["AWS-001", "AWS-007", "AWS-004"]:
            scores = get_sensor_health_details(db, st_id)
            st_name = db.query(Station.name).filter(Station.station_id == st_id).scalar()
            print(f"Station {st_id} ({st_name}):")
            for s in scores:
                print(f"  - {s['variable'].capitalize():<11}: Score={s['health_score']:5.1f} | Tier={s['status_tier']:<8} | 30d Faults={s['fault_count_30d']:<3} | Recency={s['recency_days']}d")
                print(f"    Advisory: {s['maintenance_recommendation']}")
            print("-" * 50)

        # 3. Sample 3-5 XAI Narrative Outputs for different fault types
        print("\n--- 3. Explainable AI (XAI) Narrative Outputs ---")
        fault_types = ["spike", "drift", "frozen", "missing"]
        for ft in fault_types:
            narrative = db.query(XAINarrative).filter(XAINarrative.predicted_fault_type == ft).first()
            if narrative:
                flag = db.query(AnomalyFlag).filter(AnomalyFlag.id == narrative.flag_id).first()
                print(f"Fault Type: {ft.upper()} (Station: {narrative.station_id}, Var: {narrative.variable}, TS: {narrative.timestamp})")
                print(f"  XAI Explanation Text:")
                print(f"  \"{narrative.explanation_text}\"")
                print("-" * 50)

    finally:
        db.close()

if __name__ == "__main__":
    generate_report_samples()
