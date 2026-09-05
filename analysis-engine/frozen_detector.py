import numpy as np
import pandas as pd
from config import FROZEN_WINDOW_HOURS, FROZEN_VAR_THRESHOLD

def compute_frozen_scores(df_station, variable, window_hours=FROZEN_WINDOW_HOURS, var_threshold=FROZEN_VAR_THRESHOLD):
    """
    Detects frozen sensor readings by checking rolling variance and consecutive identical values
    over a configurable trailing window (default 3 hours).
    Returns:
      - frozen_scores: pd.Series of float scores (0.0 to 5.0)
      - frozen_flagged: pd.Series of boolean flags
    """
    series = df_station[variable].copy()
    
    # 1. Compute rolling variance over trailing window_hours
    rolling_var = series.rolling(window=window_hours, min_periods=window_hours).var()
    
    # 2. Track exact consecutive diffs (value - previous_value == 0)
    diffs = series.diff().abs()
    is_zero_diff = (diffs < 1e-5) & series.notna() & series.shift(1).notna()
    
    # Count consecutive zero diffs
    consecutive_zero_count = is_zero_diff.astype(int).groupby((~is_zero_diff).cumsum()).cumsum()
    
    # Condition: rolling variance is near zero OR consecutive zero diffs >= (window_hours - 1)
    is_frozen = (rolling_var < var_threshold) | (consecutive_zero_count >= (window_hours - 1))
    is_frozen = is_frozen.fillna(False) & series.notna()
    
    scores = np.where(is_frozen, 5.0, 0.0)
    
    return pd.Series(scores, index=df_station.index), pd.Series(is_frozen, index=df_station.index)
