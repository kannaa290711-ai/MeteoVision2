import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import AnomalyFlag, GroundTruthFault, Station
from spatial_detector import haversine_km

def diagnose_false_positives():
    print("=" * 60)
    print("  AETHERIX SENTINEL - False Positive Diagnostic Audit")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Load stations metadata
        stations = db.query(Station).all()
        meta_df = pd.DataFrame([{
            "station_id": s.station_id, "name": s.name, "lat": s.lat, "lon": s.lon, "elevation_m": s.elevation_m
        } for s in stations]).set_index("station_id")
        
        # Load anomaly flags
        flags_df = pd.DataFrame([{
            "id": f.id,
            "station_id": f.station_id,
            "variable": f.variable,
            "timestamp": f.timestamp,
            "temporal_score": f.temporal_score,
            "spatial_score": f.spatial_score,
            "frozen_score": getattr(f, "frozen_score", 0.0),
            "drift_score": getattr(f, "drift_score", 0.0),
            "combined_score": f.combined_score,
            "flagged": f.flagged
        } for f in db.query(AnomalyFlag).all()])
        
        # Load ground truth faults
        faults_df = pd.DataFrame([{
            "station_id": g.station_id,
            "variable": g.variable,
            "fault_type": g.fault_type,
            "start_time": g.start_time,
            "end_time": g.end_time
        } for g in db.query(GroundTruthFault).all()])
        
        # Determine ground truth status
        flags_df["is_ground_truth"] = False
        fault_groups = faults_df.groupby(["station_id", "variable"])
        for (st_id, var), group in fault_groups:
            mask = (flags_df["station_id"] == st_id) & (flags_df["variable"] == var)
            for _, fault in group.iterrows():
                time_mask = mask & (flags_df["timestamp"] >= fault["start_time"]) & (flags_df["timestamp"] <= fault["end_time"])
                flags_df.loc[time_mask, "is_ground_truth"] = True
                
        # Isolate False Positives (Flagged == True, Ground Truth == False)
        fp_df = flags_df[(flags_df["flagged"] == True) & (flags_df["is_ground_truth"] == False)].copy()
        
        print(f"Total False Positive Flagged Points: {len(fp_df)}")
        
        # Determine triggering detector source for each FP
        fp_df["trig_temporal"] = fp_df["temporal_score"] >= 1.0
        fp_df["trig_spatial"] = fp_df["spatial_score"] >= 1.1
        fp_df["trig_frozen"] = fp_df["frozen_score"] >= 1.0
        fp_df["trig_drift"] = fp_df["drift_score"] >= 1.0
        
        def get_source_label(row):
            sources = []
            if row["trig_temporal"]: sources.append("Temporal")
            if row["trig_spatial"]: sources.append("Spatial")
            if row["trig_frozen"]: sources.append("Frozen")
            if row["trig_drift"]: sources.append("Drift")
            return " + ".join(sources) if sources else "Combined-Only"
            
        fp_df["detector_source"] = fp_df.apply(get_source_label, axis=1)
        
        # 1. Breakdown by Station ID
        print("\n--- 1. False Positives Breakdown by Station ---")
        st_summary = fp_df.groupby("station_id").size().reset_index(name="fp_count").sort_values("fp_count", ascending=False)
        st_summary["station_name"] = st_summary["station_id"].apply(lambda s: meta_df.loc[s, "name"] if s in meta_df.index else s)
        print(st_summary.to_string(index=False))
        
        # 2. Breakdown by Variable
        print("\n--- 2. False Positives Breakdown by Variable ---")
        var_summary = fp_df.groupby("variable").size().reset_index(name="fp_count")
        print(var_summary.to_string(index=False))
        
        # 3. Breakdown by Detector Source
        print("\n--- 3. False Positives Breakdown by Detector Source ---")
        source_summary = fp_df.groupby("detector_source").size().reset_index(name="fp_count").sort_values("fp_count", ascending=False)
        print(source_summary.to_string(index=False))
        
        # 4. Nearest Neighbor Distance Audit
        print("\n--- 4. Neighbor Distance Audit for Top FP Stations ---")
        st_list = list(meta_df.index)
        neighbor_distances = {}
        for st1 in st_list:
            dists = []
            for st2 in st_list:
                if st1 != st2:
                    d = haversine_km(meta_df.loc[st1, "lat"], meta_df.loc[st1, "lon"], meta_df.loc[st2, "lat"], meta_df.loc[st2, "lon"])
                    dists.append(d)
            dists.sort()
            avg_top3 = np.mean(dists[:3])
            neighbor_distances[st1] = {
                "nn1_km": round(dists[0], 2),
                "nn2_km": round(dists[1], 2),
                "nn3_km": round(dists[2], 2),
                "avg_3nn_km": round(avg_top3, 2)
            }
            
        dist_df = pd.DataFrame.from_dict(neighbor_distances, orient="index")
        dist_df.index.name = "station_id"
        merged_audit = pd.merge(st_summary, dist_df, on="station_id", how="left")
        print(merged_audit.to_string(index=False))
        print("=" * 60 + "\n")
        
        return {
            "total_fp": len(fp_df),
            "st_summary": st_summary.to_dict(orient="records"),
            "var_summary": var_summary.to_dict(orient="records"),
            "source_summary": source_summary.to_dict(orient="records")
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_false_positives()
