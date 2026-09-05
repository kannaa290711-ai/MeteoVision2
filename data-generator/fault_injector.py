import numpy as np
import pandas as pd
from datetime import timedelta

FAULT_TYPES = ["spike", "drift", "frozen", "missing"]
VARIABLES = ["temperature", "humidity", "pressure"]

def inject_faults(df_clean, target_fault_pct=0.06, seed=123):
    """
    Injects 4 types of sensor faults into raw weather readings and logs ground-truth intervals.
    Returns:
      - df_raw: pandas DataFrame with clean + injected faulty values (and NaNs for missing)
      - df_faults: pandas DataFrame of ground_truth_faults
    """
    np.random.seed(seed)
    df_raw = df_clean.copy()
    ground_truth_records = []
    
    stations = df_raw["station_id"].unique()
    
    for station_id in stations:
        st_mask = df_raw["station_id"] == station_id
        st_indices = df_raw[st_mask].index.values
        num_readings = len(st_indices)
        
        # Determine number of faults for this station (~ 10 to 15 fault events per station)
        num_fault_events = int((num_readings * target_fault_pct) / 12)  # Avg 12h per fault duration
        
        # Track occupied time ranges to avoid overlapping faults on the same variable
        occupied_slots = {v: set() for v in VARIABLES}
        
        for _ in range(num_fault_events):
            variable = np.random.choice(VARIABLES)
            fault_type = np.random.choice(FAULT_TYPES)
            
            # Duration based on fault type
            if fault_type == "spike":
                duration_hours = np.random.randint(1, 4)
            elif fault_type == "drift":
                duration_hours = np.random.randint(12, 48)
            elif fault_type == "frozen":
                duration_hours = np.random.randint(8, 24)
            elif fault_type == "missing":
                duration_hours = np.random.randint(4, 16)
            
            # Select random start index ensuring no overlap
            max_start = num_readings - duration_hours - 1
            if max_start <= 0:
                continue
                
            attempts = 0
            start_offset = None
            while attempts < 30:
                candidate = np.random.randint(0, max_start)
                slot_range = set(range(candidate, candidate + duration_hours))
                if not slot_range.intersection(occupied_slots[variable]):
                    start_offset = candidate
                    occupied_slots[variable].update(slot_range)
                    break
                attempts += 1
                
            if start_offset is None:
                continue
                
            start_idx = st_indices[start_offset]
            end_idx = st_indices[start_offset + duration_hours - 1]
            
            start_time = df_raw.loc[start_idx, "timestamp"]
            end_time = df_raw.loc[end_idx, "timestamp"]
            
            # Apply fault mutation to df_raw
            target_slice = df_raw.loc[start_idx:end_idx, variable].values
            
            if fault_type == "spike":
                # Single or multi-point large offset
                if variable == "temperature":
                    offset = np.random.choice([-1, 1]) * np.random.uniform(8.0, 15.0)
                elif variable == "humidity":
                    offset = np.random.choice([-1, 1]) * np.random.uniform(25.0, 45.0)
                else:  # pressure
                    offset = np.random.choice([-1, 1]) * np.random.uniform(10.0, 25.0)
                
                df_raw.loc[start_idx:end_idx, variable] = target_slice + offset
                
            elif fault_type == "drift":
                # Linear ramp accumulating from 0 to max_offset over duration
                if variable == "temperature":
                    max_offset = np.random.choice([-1, 1]) * np.random.uniform(6.0, 12.0)
                elif variable == "humidity":
                    max_offset = np.random.choice([-1, 1]) * np.random.uniform(20.0, 40.0)
                else:
                    max_offset = np.random.choice([-1, 1]) * np.random.uniform(8.0, 18.0)
                    
                ramp = np.linspace(0, max_offset, duration_hours)
                df_raw.loc[start_idx:end_idx, variable] = target_slice + ramp
                
            elif fault_type == "frozen":
                # Repeat exact same value constant for duration_hours
                frozen_value = target_slice[0]
                df_raw.loc[start_idx:end_idx, variable] = frozen_value
                
            elif fault_type == "missing":
                # Data dropout: NaN / None
                df_raw.loc[start_idx:end_idx, variable] = np.nan
                
            # Log ground truth record
            ground_truth_records.append({
                "station_id": station_id,
                "variable": variable,
                "fault_type": fault_type,
                "start_time": start_time,
                "end_time": end_time
            })
            
    df_faults = pd.DataFrame(ground_truth_records)
    return df_raw, df_faults
