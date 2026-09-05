import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Path setup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, RawReading, AnomalyFlag, ImputedReading
from config import IMPUTATION_CONFIDENCE_THRESHOLD, SPATIAL_K_NEIGHBORS
from physics_checker import check_physics_bounds

STD_DEV_MAP = {
    "temperature": 3.0,
    "humidity": 8.0,
    "pressure": 4.0
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0)**2
    return 2.0 * R * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))

def compute_idw_spatial(station_id, variable, timestamp, readings_by_ts, stations_df):
    target_st = stations_df.loc[station_id]
    ts_readings = readings_by_ts.get((timestamp, variable), {})
    
    weights, values = [], []
    for other_id, st in stations_df.iterrows():
        if other_id == station_id:
            continue
        val = ts_readings.get(other_id)
        if val is not None and not np.isnan(val):
            dist = haversine(target_st["lat"], target_st["lon"], st["lat"], st["lon"])
            dist = max(dist, 0.1)  # prevent division by zero
            w = 1.0 / (dist ** 2)
            weights.append(w)
            values.append(val)
            
    if not values:
        return None
        
    weights = np.array(weights)
    values = np.array(values)
    return float(np.sum(weights * values) / np.sum(weights))

def compute_temporal_interpolation(station_id, variable, timestamp, station_timeseries):
    ts_list = station_timeseries.get((station_id, variable), pd.Series(dtype=float))
    if ts_list.empty:
        return None
        
    prev_readings = ts_list[ts_list.index < timestamp].tail(3)
    next_readings = ts_list[ts_list.index > timestamp].head(3)
    
    if prev_readings.empty and next_readings.empty:
        return None
    elif prev_readings.empty:
        return float(next_readings.iloc[0])
    elif next_readings.empty:
        return float(prev_readings.iloc[-1])
    else:
        t0, v0 = prev_readings.index[-1], prev_readings.iloc[-1]
        t1, v1 = next_readings.index[0], next_readings.iloc[0]
        
        dt_total = (t1 - t0).total_seconds()
        if dt_total == 0:
            return float(v0)
        dt_target = (timestamp - t0).total_seconds()
        frac = dt_target / dt_total
        return float(v0 + frac * (v1 - v0))

def compute_drift_pre_onset(station_id, variable, timestamp, station_timeseries, diurnal_profiles):
    hour = timestamp.hour
    baseline_val = diurnal_profiles.get((station_id, variable, hour))
    
    ts_list = station_timeseries.get((station_id, variable), pd.Series(dtype=float))
    pre_drift = ts_list[ts_list.index < (timestamp - timedelta(hours=12))].tail(6)
    
    if not pre_drift.empty and baseline_val is not None:
        offset = float(pre_drift.mean() - baseline_val)
        return baseline_val + offset
    elif baseline_val is not None:
        return float(baseline_val)
    elif not pre_drift.empty:
        return float(pre_drift.mean())
    return None

def run_self_healing_imputation():
    print("=" * 65)
    print("  AETHERIX SENTINEL - Phase 3 Self-Healing Imputation Engine")
    print("=" * 65)
    
    db = SessionLocal()
    try:
        stations = db.query(Station).all()
        stations_df = pd.DataFrame([{
            "station_id": s.station_id, "lat": s.lat, "lon": s.lon, "elevation_m": s.elevation_m
        } for s in stations]).set_index("station_id")
        
        print("[1/4] Loading raw readings & computing spatial-temporal lookups...")
        raw_readings = db.query(RawReading).all()
        
        readings_by_ts = {}  # (timestamp, variable) -> {station_id: val}
        station_timeseries = {} # (station_id, variable) -> pd.Series(index=timestamp, data=val)
        
        records = []
        for r in raw_readings:
            records.extend([
                {"station_id": r.station_id, "timestamp": r.timestamp, "variable": "temperature", "value": r.temperature, "reading_id": r.id},
                {"station_id": r.station_id, "timestamp": r.timestamp, "variable": "humidity", "value": r.humidity, "reading_id": r.id},
                {"station_id": r.station_id, "timestamp": r.timestamp, "variable": "pressure", "value": r.pressure, "reading_id": r.id},
            ])
            
            for var, val in [("temperature", r.temperature), ("humidity", r.humidity), ("pressure", r.pressure)]:
                key = (r.timestamp, var)
                if key not in readings_by_ts:
                    readings_by_ts[key] = {}
                if val is not None:
                    readings_by_ts[key][r.station_id] = val
                    
        df_records = pd.DataFrame(records)
        for (st_id, var), group in df_records.groupby(["station_id", "variable"]):
            clean_group = group.dropna(subset=["value"]).sort_values("timestamp")
            station_timeseries[(st_id, var)] = pd.Series(clean_group["value"].values, index=clean_group["timestamp"])
            
        diurnal_profiles = df_records.dropna(subset=["value"]).groupby(
            ["station_id", "variable", df_records["timestamp"].dt.hour]
        )["value"].mean().to_dict()
        
        print(f"[2/4] Querying faulty readings requiring imputation (ML confidence >= {IMPUTATION_CONFIDENCE_THRESHOLD:.2f})...")
        target_flags = db.query(AnomalyFlag).filter(
            AnomalyFlag.predicted_fault_type != "none",
            AnomalyFlag.ml_confidence >= IMPUTATION_CONFIDENCE_THRESHOLD
        ).all()
        
        print(f"      Found {len(target_flags)} faulty flags eligible for self-healing.")
        
        db.query(ImputedReading).delete()
        db.commit()
        
        imputed_records = []
        
        print("[3/4] Running multi-method self-healing & physics checks...")
        for flag in target_flags:
            st_id = flag.station_id
            var = flag.variable
            ts = flag.timestamp
            fault = flag.predicted_fault_type
            conf = flag.ml_confidence
            
            raw_val = readings_by_ts.get((ts, var), {}).get(st_id)
            v_spatial = compute_idw_spatial(st_id, var, ts, readings_by_ts, stations_df)
            
            if fault == "drift":
                v_temporal = compute_drift_pre_onset(st_id, var, ts, station_timeseries, diurnal_profiles)
                imputation_method = "pre_onset_extrapolation"
                if v_temporal is not None and v_spatial is not None:
                    estimated_val = 0.7 * v_temporal + 0.3 * v_spatial
                elif v_temporal is not None:
                    estimated_val = v_temporal
                else:
                    estimated_val = v_spatial
            elif fault == "missing":
                v_temporal = compute_temporal_interpolation(st_id, var, ts, station_timeseries)
                imputation_method = "extended_gap_blend"
                if v_spatial is not None and v_temporal is not None:
                    estimated_val = 0.6 * v_spatial + 0.4 * v_temporal
                elif v_spatial is not None:
                    estimated_val = v_spatial
                else:
                    estimated_val = v_temporal
            else:  # spike / frozen
                v_temporal = compute_temporal_interpolation(st_id, var, ts, station_timeseries)
                imputation_method = "blend_idw_linear"
                if v_spatial is not None and v_temporal is not None:
                    estimated_val = 0.5 * v_spatial + 0.5 * v_temporal
                elif v_spatial is not None:
                    estimated_val = v_spatial
                else:
                    estimated_val = v_temporal
                    
            if estimated_val is None:
                estimated_val = 25.0 if var == "temperature" else (65.0 if var == "humidity" else 950.0)
                
            # Corrected Imputation Confidence Calculation
            std_v = STD_DEV_MAP.get(var, 5.0)
            if v_spatial is not None and v_temporal is not None:
                delta = abs(v_spatial - v_temporal)
                # Agreement ratio A based on spatial vs temporal delta
                agreement = max(0.0, 1.0 - (delta / (1.2 * std_v)))
            else:
                agreement = 0.5
                
            if fault == "missing":
                # For missing values, imputation confidence is derived strictly from estimate agreement & gap stability
                imputation_conf = max(0.40, min(0.98, agreement * 0.95))
            else:
                # For other fault types, combine classification confidence with estimate agreement
                imputation_conf = max(0.40, min(0.98, conf * (0.60 + 0.40 * agreement)))
            
            # Physics Sanity Check
            elevation = stations_df.loc[st_id, "elevation_m"] if st_id in stations_df.index else 500.0
            paired_vals = {
                v_other: readings_by_ts.get((ts, v_other), {}).get(st_id)
                for v_other in ["temperature", "humidity", "pressure"] if v_other != var
            }
            phys_passed, phys_details = check_physics_bounds(var, estimated_val, elevation, paired_vals)
            
            if phys_passed:
                status_label = f"AI-Estimated/Imputed (confidence: {imputation_conf*100:.0f}%)"
            else:
                status_label = "Needs Manual Review"
                
            imputed_records.append({
                "flag_id": flag.id,
                "reading_id": flag.reading_id,
                "station_id": st_id,
                "variable": var,
                "timestamp": ts,
                "raw_value": raw_val,
                "estimated_value": round(float(estimated_val), 2),
                "imputation_method": imputation_method,
                "spatial_estimate": round(float(v_spatial), 2) if v_spatial is not None else None,
                "temporal_estimate": round(float(v_temporal), 2) if v_temporal is not None else None,
                "imputation_confidence": round(float(imputation_conf), 4),
                "physics_check_passed": phys_passed,
                "physics_check_details": phys_details,
                "status_label": status_label
            })
            
        print("[4/4] Saving imputed records to database...")
        db.bulk_insert_mappings(ImputedReading, imputed_records)
        db.commit()
        print(f"      Successfully generated & stored {len(imputed_records)} self-healed records in `imputed_readings`!")
        print("=" * 65 + "\n")
        
        return imputed_records
        
    finally:
        db.close()

if __name__ == "__main__":
    run_self_healing_imputation()
