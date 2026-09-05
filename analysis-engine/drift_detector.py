import numpy as np
import pandas as pd
from diurnal_baseline import compute_hourly_diurnal_baseline
from spatial_detector import haversine_km
from config import DRIFT_WINDOW_HOURS, CUSUM_K, CUSUM_H, DRIFT_SUSTAINED_HOURS

def compute_spatial_diurnal_drift_scores(df_all, stations_meta, variable, window_hours=DRIFT_WINDOW_HOURS, cusum_k=1.2, cusum_h=8.0, sustained_hours=8):
    """
    Computes station-specific sensor drift using Spatial-Diurnal Residual CUSUM.
    Subtracts the regional synoptic weather wave (IDW of neighbors' diurnal residuals) 
    so regional heatwaves/cloud cover do not trigger false drift flags.
    """
    meta_df = pd.DataFrame(stations_meta).set_index("station_id")
    stations = list(meta_df.index)
    
    # 1. Compute diurnal residual per station
    pivoted = df_all.pivot(index="timestamp", columns="station_id", values=variable)
    diurnal_residuals = pd.DataFrame(index=pivoted.index, columns=stations, dtype=float)
    
    for st in stations:
        st_df = df_all[df_all["station_id"] == st].sort_values("timestamp")
        base = compute_hourly_diurnal_baseline(st_df, variable, trailing_days=14)
        diurnal_residuals[st] = (st_df.set_index("timestamp")[variable] - base.values).reindex(pivoted.index)
        
    # 2. Subtract regional synoptic wave via spatial IDW of neighbor diurnal residuals
    # Distance matrix
    dist_matrix = {s1: {s2: 0.0 if s1 == s2 else haversine_km(meta_df.loc[s1, "lat"], meta_df.loc[s1, "lon"], meta_df.loc[s2, "lat"], meta_df.loc[s2, "lon"]) for s2 in stations} for s1 in stations}
    
    station_specific_drift_res = pd.DataFrame(index=pivoted.index, columns=stations, dtype=float)
    
    for st in stations:
        other_stations = [s for s in stations if s != st]
        distances = pd.Series({s: dist_matrix[st][s] for s in other_stations})
        nearest = distances.nsmallest(3)
        
        weights = 1.0 / (nearest ** 2.0)
        neighbor_res = diurnal_residuals[nearest.index]
        
        weighted_res = neighbor_res.mul(weights, axis=1)
        sum_weights = neighbor_res.notna().mul(weights, axis=1).sum(axis=1)
        
        regional_wave = weighted_res.sum(axis=1) / sum_weights.replace(0, np.nan)
        # Station-specific residual = station diurnal residual - regional synoptic wave
        station_specific_drift_res[st] = diurnal_residuals[st] - regional_wave
        
    # 3. Run CUSUM on station-specific drift residual per station
    drift_score_df = pd.DataFrame(index=pivoted.index, columns=stations, dtype=float)
    drift_flag_df = pd.DataFrame(index=pivoted.index, columns=stations, dtype=bool)
    
    for st in stations:
        res = station_specific_drift_res[st]
        num_pts = len(res)
        
        std_r = res.rolling(window=24, min_periods=6).std().replace(0, 1e-4)
        z_vals = (res / std_r).fillna(0.0).values
        
        s_pos = np.zeros(num_pts)
        s_neg = np.zeros(num_pts)
        
        for i in range(1, num_pts):
            if z_vals[i] * z_vals[i-1] < 0:
                s_pos[i-1] = 0.0
                s_neg[i-1] = 0.0
            s_pos[i] = max(0.0, s_pos[i-1] + z_vals[i] - cusum_k)
            s_neg[i] = max(0.0, s_neg[i-1] - z_vals[i] - cusum_k)
            
        c_max = np.maximum(s_pos, s_neg)
        c_exceeded = pd.Series(c_max >= cusum_h, index=pivoted.index)
        
        c_sustained = (c_exceeded.rolling(window=sustained_hours, min_periods=sustained_hours).min() == 1.0).fillna(False)
        is_drift_st = c_sustained & pivoted[st].notna()
        
        score_st = np.where(is_drift_st, np.maximum(c_max / cusum_h, 1.2), np.minimum(c_max / cusum_h, 0.8))
        
        drift_score_df[st] = score_st
        drift_flag_df[st] = is_drift_st
        
    # Unpivot scores and flags back to df_all order
    long_scores = drift_score_df.stack(future_stack=True).reset_index()
    long_scores.columns = ["timestamp", "station_id", "drift_score"]
    
    long_flags = drift_flag_df.stack(future_stack=True).reset_index()
    long_flags.columns = ["timestamp", "station_id", "drift_flagged"]
    
    merged = pd.merge(df_all[["station_id", "timestamp"]], long_scores, on=["station_id", "timestamp"], how="left")
    merged = pd.merge(merged, long_flags, on=["station_id", "timestamp"], how="left")
    
    return merged["drift_score"].fillna(0.0), merged["drift_flagged"].fillna(False)
