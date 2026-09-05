import numpy as np
import pandas as pd

def compute_temporal_scores(df_station, variable, window_size=24, min_mad=1e-4):
    """
    Computes rolling modified Z-score (median & MAD) for a single station's readings.
    Handles zero variance (frozen sensor) detection.
    Returns: pandas Series of temporal anomaly scores (normalized: >= 1.0 indicates anomaly).
    """
    series = df_station[variable].copy()
    
    # Missing values (NaNs) are instant temporal anomalies (score = 5.0)
    missing_mask = series.isna()
    
    # Rolling Median and MAD
    rolling_med = series.rolling(window=window_size, min_periods=3, center=True).median()
    rolling_mad = (series - rolling_med).abs().rolling(window=window_size, min_periods=3, center=True).median()
    
    # Modified Z-score formula: 0.6745 * |x - median| / MAD
    dev = (series - rolling_med).abs()
    
    # Calculate Modified Z-Score
    # Avoid division by zero when MAD is ~0 (e.g. frozen value)
    safe_mad = np.maximum(rolling_mad.values, min_mad)
    mod_z = 0.6745 * dev.values / safe_mad
    
    # Handle frozen sensor (MAD is near 0 for >= 6 consecutive hours)
    frozen_mask = (rolling_mad.values < min_mad) & ~missing_mask.values
    
    # Normalize score: threshold is typically 3.5 for Modified Z-Score
    norm_score = mod_z / 3.5
    
    # Assign high score for missing and frozen data
    norm_score[missing_mask.values] = 5.0
    norm_score[frozen_mask] = 4.0
    
    # Fill remaining NaNs at boundaries
    norm_score = np.nan_to_num(norm_score, nan=0.0)
    
    return pd.Series(norm_score, index=df_station.index)
