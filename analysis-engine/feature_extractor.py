import numpy as np
import pandas as pd
from spatial_detector import haversine_km
from diurnal_baseline import compute_hourly_diurnal_baseline

def compute_spatial_consensus_features(df_all, stations_meta, variable, k_neighbors=3):
    """
    Computes neighbor_agreement feature for each reading.
    neighbor_agreement: fraction (0.0 to 1.0) of N nearest neighbors showing 
    similar-direction, similar-magnitude deviation in the same time window.
    High agreement = regional weather event (synoptic wave); Low agreement = isolated sensor fault.
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
        
    # Distance matrix
    dist_matrix = {s1: {s2: 0.0 if s1 == s2 else haversine_km(meta_df.loc[s1, "lat"], meta_df.loc[s1, "lon"], meta_df.loc[s2, "lat"], meta_df.loc[s2, "lon"]) for s2 in stations} for s1 in stations}
    
    agreement_df = pd.DataFrame(index=pivoted.index, columns=stations, dtype=float)
    
    for st in stations:
        other_stations = [s for s in stations if s != st]
        distances = pd.Series({s: dist_matrix[st][s] for s in other_stations})
        nearest = distances.nsmallest(k_neighbors).index.tolist()
        
        target_res = diurnal_residuals[st]
        neighbor_res_matrix = diurnal_residuals[nearest]
        
        # Agreement condition: neighbor residual has SAME sign as target AND magnitude >= 40% of target magnitude
        target_sign = np.sign(target_res.values)[:, None]  # Shape: (T, 1)
        neighbor_signs = np.sign(neighbor_res_matrix.values) # Shape: (T, K)
        
        target_abs = np.abs(target_res.values)[:, None]
        neighbor_abs = np.abs(neighbor_res_matrix.values)
        
        # Match mask: sign matches AND neighbor has meaningful deviation (> 0.5 * target or > 1.0 unit)
        sign_match = (target_sign == neighbor_signs) & (target_sign != 0)
        mag_match = (neighbor_abs >= 0.4 * target_abs) | (neighbor_abs >= 1.0)
        
        agreed_matrix = sign_match & mag_match
        
        # Fraction of neighbors agreeing
        agreement_ratio = agreed_matrix.mean(axis=1)
        
        # If target has near-zero deviation (|target_res| < 1.0), default agreement is 1.0 (normal background)
        normal_bg_mask = np.abs(target_res.values) < 1.0
        agreement_ratio[normal_bg_mask] = 1.0
        
        agreement_df[st] = agreement_ratio
        
    # Unpivot back to df_all order
    long_agreement = agreement_df.stack(future_stack=True).reset_index()
    long_agreement.columns = ["timestamp", "station_id", "neighbor_agreement"]
    
    merged = pd.merge(df_all[["station_id", "timestamp"]], long_agreement, on=["station_id", "timestamp"], how="left")
    return merged["neighbor_agreement"].fillna(1.0)
