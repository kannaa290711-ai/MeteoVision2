import sys
import os
import pandas as pd
import numpy as np

# Add paths
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from backend.app.models import Station, RawReading, AnomalyFlag
from temporal_detector import compute_temporal_scores
from spatial_detector import compute_spatial_scores
from frozen_detector import compute_frozen_scores
from drift_detector import compute_spatial_diurnal_drift_scores
from feature_extractor import compute_spatial_consensus_features

VARIABLES = ["temperature", "humidity", "pressure"]

def run_anomaly_detection_pipeline():
    print("=" * 60)
    print("  AETHERIX SENTINEL - Integrated Multi-Detector & Feature Pipeline")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        print("[1/5] Loading stations and raw readings from database...")
        stations_query = db.query(Station).all()
        stations_meta = [
            {
                "station_id": s.station_id,
                "name": s.name,
                "lat": s.lat,
                "lon": s.lon,
                "elevation_m": s.elevation_m
            }
            for s in stations_query
        ]
        
        readings_query = db.query(RawReading).all()
        readings_data = [
            {
                "id": r.id,
                "station_id": r.station_id,
                "timestamp": r.timestamp,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "pressure": r.pressure
            }
            for r in readings_query
        ]
        df_readings = pd.DataFrame(readings_data)
        print(f"      Loaded {len(df_readings)} raw readings across {len(stations_meta)} stations.")
        
        all_flag_objs = []
        
        for var in VARIABLES:
            print(f"[2/5] Extracting Temporal, Spatial, Frozen, Drift & Spatial-Consensus features for '{var}'...")
            
            # --- 1. Temporal Detection ---
            df_readings[f"{var}_temporal"] = 0.0
            # --- 3. Frozen Detection ---
            df_readings[f"{var}_frozen"] = 0.0
            
            for st_meta in stations_meta:
                st_id = st_meta["station_id"]
                st_mask = df_readings["station_id"] == st_id
                df_st = df_readings[st_mask].sort_values("timestamp")
                
                # Temporal
                t_scores = compute_temporal_scores(df_st, var, window_size=24)
                df_readings.loc[df_st.index, f"{var}_temporal"] = t_scores.values
                
                # Frozen
                fz_scores, _ = compute_frozen_scores(df_st, var, window_hours=3)
                df_readings.loc[df_st.index, f"{var}_frozen"] = fz_scores.values
                
            # --- 2. Spatial Detection ---
            s_scores = compute_spatial_scores(df_readings, stations_meta, var, k_neighbors=3)
            df_readings[f"{var}_spatial"] = s_scores.values
            
            # --- 4. Spatial-Diurnal CUSUM Drift Detection ---
            dr_scores, dr_flags = compute_spatial_diurnal_drift_scores(df_readings, stations_meta, var, cusum_k=1.2, cusum_h=8.0, sustained_hours=8)
            df_readings[f"{var}_drift"] = dr_scores.values
            
            # --- 5. Spatial Consensus Neighbor Agreement Feature ---
            ag_scores = compute_spatial_consensus_features(df_readings, stations_meta, var, k_neighbors=3)
            df_readings[f"{var}_neighbor_agreement"] = ag_scores.values
            
            # --- Combined Score & Heuristic Flagging (will be replaced by ML classifier) ---
            temp_s = df_readings[f"{var}_temporal"]
            spat_s = df_readings[f"{var}_spatial"]
            froz_s = df_readings[f"{var}_frozen"]
            drft_s = df_readings[f"{var}_drift"]
            
            max_s = np.maximum.reduce([temp_s, spat_s, froz_s, drft_s])
            avg_s = (temp_s + spat_s + froz_s + drft_s) / 4.0
            comb_s = max_s * 0.7 + avg_s * 0.3
            df_readings[f"{var}_combined"] = comb_s.round(3)
            
            flagged = (temp_s >= 1.2) | (spat_s >= 1.4) | (froz_s >= 1.0) | (drft_s >= 1.0)
            df_readings[f"{var}_flagged"] = flagged
            
            # Prepare AnomalyFlag ORM objects
            for idx, row in df_readings.iterrows():
                obj = AnomalyFlag(
                    reading_id=int(row["id"]),
                    station_id=row["station_id"],
                    variable=var,
                    timestamp=row["timestamp"],
                    temporal_score=float(row[f"{var}_temporal"]),
                    spatial_score=float(row[f"{var}_spatial"]),
                    frozen_score=float(row[f"{var}_frozen"]),
                    drift_score=float(row[f"{var}_drift"]),
                    neighbor_agreement=float(row[f"{var}_neighbor_agreement"]),
                    combined_score=float(row[f"{var}_combined"]),
                    flagged=bool(row[f"{var}_flagged"]),
                    predicted_fault_type="none",
                    ml_confidence=0.0
                )
                all_flag_objs.append(obj)
                
        print(f"[3/5] Recreating anomaly_flags table with new columns...")
        AnomalyFlag.__table__.drop(bind=engine, checkfirst=True)
        AnomalyFlag.__table__.create(bind=engine)
        
        print(f"      Saving {len(all_flag_objs)} anomaly flag evaluations & features to DB...")
        chunk_size = 5000
        for i in range(0, len(all_flag_objs), chunk_size):
            db.bulk_save_objects(all_flag_objs[i:i+chunk_size])
            db.commit()
            
        print(f"[4/5] Multi-detector & Feature pipeline completed successfully!")
        print(f"      Total Feature Records Extracted: {len(all_flag_objs)}")
        print("=" * 60 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_anomaly_detection_pipeline()
