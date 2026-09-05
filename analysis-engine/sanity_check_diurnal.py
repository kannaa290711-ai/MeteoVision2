import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import RawReading, GroundTruthFault
from diurnal_baseline import compute_hourly_diurnal_baseline

def run_diurnal_sanity_gate():
    print("=" * 60)
    print("  PART 4 SANITY GATE - Diurnal Baseline & Residual Check")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Load readings for AWS-001
        st_id = "AWS-001"
        readings = db.query(RawReading).filter(RawReading.station_id == st_id).order_by(RawReading.timestamp).all()
        df_st = pd.DataFrame([{
            "timestamp": r.timestamp,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "pressure": r.pressure
        } for r in readings])
        
        # Compute diurnal baseline
        baseline = compute_hourly_diurnal_baseline(df_st, "temperature", trailing_days=14)
        df_st["diurnal_baseline"] = baseline
        df_st["diurnal_residual"] = (df_st["temperature"] - baseline).round(2)
        
        # 1. Clean Day (No Faults) - Sample March 15, 2026
        clean_mask = (df_st["timestamp"] >= "2026-03-15 00:00:00") & (df_st["timestamp"] <= "2026-03-15 23:00:00")
        df_clean = df_st[clean_mask].copy()
        
        print("\n--- 24-Hour Cycle on NORMAL Day (2026-03-15, AWS-001 Temp) ---")
        print(f"{'Hour':<6} | {'Actual Temp (°C)':<16} | {'Diurnal Base (°C)':<18} | {'Residual (°C)':<14}")
        print("-" * 62)
        for _, row in df_clean.iterrows():
            hr = row["timestamp"].strftime("%H:00")
            print(f"{hr:<6} | {row['temperature']:<16.2f} | {row['diurnal_baseline']:<18.2f} | {row['diurnal_residual']:<14.2f}")
            
        print(f"\nNormal Day Summary -> Mean Residual: {df_clean['diurnal_residual'].mean():.2f}°C | Max Residual: {df_clean['diurnal_residual'].abs().max():.2f}°C")
        
        # 2. Drift Fault Day - Find an injected drift fault for temperature
        drift_fault = db.query(GroundTruthFault).filter(
            GroundTruthFault.fault_type == "drift",
            GroundTruthFault.variable == "temperature"
        ).first()
        
        if drift_fault:
            d_st = drift_fault.station_id
            d_start = drift_fault.start_time
            d_end = drift_fault.end_time
            
            d_readings = db.query(RawReading).filter(RawReading.station_id == d_st).order_by(RawReading.timestamp).all()
            df_drift_st = pd.DataFrame([{
                "timestamp": r.timestamp,
                "temperature": r.temperature
            } for r in d_readings])
            
            d_base = compute_hourly_diurnal_baseline(df_drift_st, "temperature", trailing_days=14)
            df_drift_st["diurnal_baseline"] = d_base
            df_drift_st["diurnal_residual"] = (df_drift_st["temperature"] - d_base).round(2)
            
            fault_mask = (df_drift_st["timestamp"] >= d_start) & (df_drift_st["timestamp"] <= d_end)
            df_fault_sample = df_drift_st[fault_mask].copy()
            
            print(f"\n--- 24-Hour Cycle during INJECTED DRIFT FAULT ({d_st}, {d_start} to {d_end}) ---")
            print(f"{'Timestamp':<19} | {'Actual Temp (°C)':<16} | {'Diurnal Base (°C)':<18} | {'Residual (°C)':<14}")
            print("-" * 75)
            for _, row in df_fault_sample.head(12).iterrows():
                ts_str = row["timestamp"].strftime("%Y-%m-%d %H:00")
                print(f"{ts_str:<19} | {row['temperature']:<16.2f} | {row['diurnal_baseline']:<18.2f} | {row['diurnal_residual']:<14.2f}")
                
            print(f"\nDrift Fault Day Summary -> Mean Residual: {df_fault_sample['diurnal_residual'].mean():.2f}°C | Max Residual: {df_fault_sample['diurnal_residual'].abs().max():.2f}°C")
            
        print("=" * 60 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_diurnal_sanity_gate()
