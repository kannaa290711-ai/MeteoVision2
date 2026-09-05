import numpy as np
import pandas as pd

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Computes Haversine distance in kilometers between two lat/lon points.
    """
    R = 6371.0  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def normalize_variable_for_elevation(values, elev_series, variable):
    """
    Normalizes temperature and pressure to sea-level equivalent for spatially fair comparison across mountain/valley stations.
    """
    if variable == "temperature":
        # Lapse rate: add back 0.65°C per 100m elevation
        return values + (elev_series * 0.0065)
    elif variable == "pressure":
        # MSLP conversion
        factor = (1.0 - (0.0065 * elev_series / 288.15)) ** 5.2558
        return values / factor
    return values.copy()


def denormalize_variable_for_elevation(norm_values, elev_series, variable):
    """
    Converts sea-level normalized estimate back to station station elevation.
    """
    if variable == "temperature":
        return norm_values - (elev_series * 0.0065)
    elif variable == "pressure":
        factor = (1.0 - (0.0065 * elev_series / 288.15)) ** 5.2558
        return norm_values * factor
    return norm_values.copy()


def compute_spatial_scores(df_all, stations_meta, variable, k_neighbors=3, power=2.0):
    """
    Computes spatial anomaly score for all stations using Inverse Distance Weighting (IDW) 
    with elevation lapse rate normalization.
    """
    meta_df = pd.DataFrame(stations_meta).set_index("station_id")
    stations = list(meta_df.index)
    
    # Distance matrix
    dist_matrix = {}
    for st1 in stations:
        dist_matrix[st1] = {}
        for st2 in stations:
            if st1 == st2:
                dist_matrix[st1][st2] = 0.0
            else:
                lat1, lon1 = meta_df.loc[st1, "lat"], meta_df.loc[st1, "lon"]
                lat2, lon2 = meta_df.loc[st2, "lat"], meta_df.loc[st2, "lon"]
                dist_matrix[st1][st2] = haversine_km(lat1, lon1, lat2, lon2)
                
    pivoted = df_all.pivot(index="timestamp", columns="station_id", values=variable)
    
    # Normalize variable for station elevation
    pivoted_norm = pivoted.copy()
    for st in stations:
        elev = meta_df.loc[st, "elevation_m"]
        pivoted_norm[st] = normalize_variable_for_elevation(pivoted[st], elev, variable)
        
    noise_thresholds = {
        "temperature": 2.5,   # °C residual threshold
        "humidity": 12.0,     # % residual threshold
        "pressure": 3.0       # hPa residual threshold
    }
    threshold = noise_thresholds.get(variable, 2.5)
    
    idw_estimates = pd.DataFrame(index=pivoted.index, columns=stations, dtype=float)
    
    for st in stations:
        elev = meta_df.loc[st, "elevation_m"]
        other_stations = [s for s in stations if s != st]
        distances = pd.Series({s: dist_matrix[st][s] for s in other_stations})
        nearest = distances.nsmallest(k_neighbors)
        
        weights = 1.0 / (nearest ** power)
        neighbor_vals = pivoted_norm[nearest.index]
        
        weighted_vals = neighbor_vals.mul(weights, axis=1)
        sum_weights = neighbor_vals.notna().mul(weights, axis=1).sum(axis=1)
        
        norm_estimate = weighted_vals.sum(axis=1) / sum_weights.replace(0, np.nan)
        # Denormalize estimate back to target station's elevation
        idw_estimates[st] = denormalize_variable_for_elevation(norm_estimate, elev, variable)
        
    residuals = (pivoted - idw_estimates).abs()
    spatial_score_df = residuals / threshold
    
    for st in stations:
        spatial_score_df.loc[pivoted[st].isna(), st] = 5.0
        
    long_scores = spatial_score_df.stack(future_stack=True).reset_index()
    long_scores.columns = ["timestamp", "station_id", "spatial_score"]
    
    merged = pd.merge(
        df_all[["station_id", "timestamp"]],
        long_scores,
        on=["station_id", "timestamp"],
        how="left"
    )
    
    merged["spatial_score"] = merged["spatial_score"].fillna(0.0)
    return merged["spatial_score"]
