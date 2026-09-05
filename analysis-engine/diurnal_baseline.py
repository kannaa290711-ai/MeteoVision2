import numpy as np
import pandas as pd

def compute_hourly_diurnal_baseline(df_station, variable, trailing_days=14):
    """
    Computes expected value profile by hour-of-day (0-23) using a trailing rolling window of clean readings.
    Returns: pd.Series of expected diurnal values aligned with df_station.index.
    """
    series = df_station[variable].copy()
    timestamps = df_station["timestamp"]
    hours = timestamps.dt.hour
    
    # 1. Mask extreme outliers (|z| > 3.5) to avoid contaminating baseline
    med = series.median()
    mad = (series - med).abs().median()
    if mad > 1e-4:
        clean_series = series.where((0.6745 * (series - med).abs() / mad) < 3.5)
    else:
        clean_series = series.copy()
        
    df_temp = pd.DataFrame({
        "timestamp": timestamps,
        "hour": hours,
        "val": clean_series
    })
    
    # 2. For each hour-of-day, compute trailing rolling mean over trailing_days
    # Compute average by (hour) over trailing window
    diurnal_baseline = pd.Series(index=df_station.index, dtype=float)
    
    # Pre-calculate hour-of-day overall profile as fallback for initial days
    hour_overall_profile = df_temp.groupby("hour")["val"].transform("mean")
    
    # Compute rolling hourly mean per hour group
    grouped_rolling = df_temp.groupby("hour")["val"].transform(
        lambda s: s.rolling(window=trailing_days, min_periods=2).mean()
    )
    
    # Fill initial days with hour overall profile
    diurnal_baseline = grouped_rolling.fillna(hour_overall_profile).fillna(series.median())
    
    return diurnal_baseline
