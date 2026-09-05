import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from backend.app.models import Station, RawReading, GroundTruthFault
from generator import STATIONS, generate_clean_weather_data
from fault_injector import inject_faults


def seed_database(days=180):
    print("=" * 60)
    print("  AETHERIX SENTINEL - Synthetic Data Generator & DB Seed")
    print("=" * 60)
    
    # 1. Reset and Create Tables
    print("[1/5] Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Seed Stations
        print("[2/5] Seeding 12 AWS Stations...")
        station_objs = []
        for st in STATIONS:
            obj = Station(
                station_id=st["station_id"],
                name=st["name"],
                lat=st["lat"],
                lon=st["lon"],
                elevation_m=st["elevation_m"]
            )
            station_objs.append(obj)
        db.bulk_save_objects(station_objs)
        db.commit()
        print(f"      Successfully seeded {len(station_objs)} stations.")
        
        # 3. Generate Clean Weather Data
        print(f"[3/5] Generating {days} days of clean hourly weather readings...")
        df_clean = generate_clean_weather_data(start_date="2026-03-01", days=days, seed=42)
        print(f"      Generated {len(df_clean)} raw weather records across all stations.")
        
        # 4. Inject Faults
        print("[4/5] Injecting sensor faults (Spike, Drift, Frozen, Missing)...")
        df_raw, df_faults = inject_faults(df_clean, target_fault_pct=0.08, seed=123)
        print(f"      Injected {len(df_faults)} fault intervals into data.")
        
        # 5. Populate Database
        print("[5/5] Writing raw_readings and ground_truth_faults to DB...")
        
        # Save raw readings in chunks
        chunk_size = 5000
        raw_records = df_raw.to_dict(orient="records")
        for i in range(0, len(raw_records), chunk_size):
            chunk = [
                RawReading(
                    station_id=r["station_id"],
                    timestamp=r["timestamp"],
                    temperature=r["temperature"] if pd.notnull(r["temperature"]) else None,
                    humidity=r["humidity"] if pd.notnull(r["humidity"]) else None,
                    pressure=r["pressure"] if pd.notnull(r["pressure"]) else None
                )
                for r in raw_records[i:i+chunk_size]
            ]
            db.bulk_save_objects(chunk)
            db.commit()
            
        # Save ground truth faults
        fault_records = df_faults.to_dict(orient="records")
        fault_objs = [
            GroundTruthFault(
                station_id=r["station_id"],
                variable=r["variable"],
                fault_type=r["fault_type"],
                start_time=r["start_time"],
                end_time=r["end_time"]
            )
            for r in fault_records
        ]
        db.bulk_save_objects(fault_objs)
        db.commit()
        
        # SANITY CHECK PRINTOUT
        print("\n" + "=" * 60)
        print("  PART 1 SANITY CHECK & DATA STATS SUMMARY")
        print("=" * 60)
        print(f"Total Stations:       {db.query(Station).count()}")
        print(f"Total Raw Readings:   {db.query(RawReading).count()}")
        print(f"Total Logged Faults:  {db.query(GroundTruthFault).count()}")
        
        print("\nFault Counts by Type & Variable:")
        fault_summary = df_faults.groupby(["fault_type", "variable"]).size().unstack(fill_value=0)
        print(fault_summary)
        
        print("\nSample Ground Truth Fault Records (First 5):")
        print(df_faults.head(5).to_string(index=False))
        
        print("\nReadings Statistics (Clean vs Faulty Range):")
        print(df_raw[["temperature", "humidity", "pressure"]].describe())
        print("=" * 60 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
