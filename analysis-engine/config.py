"""
AETHERIX SENTINEL - Detection Engine Configuration Parameters
"""

# Temporal Detector Parameters
TEMPORAL_WINDOW_HOURS = 24
TEMPORAL_Z_THRESHOLD = 3.5

# Spatial Detector Parameters
SPATIAL_K_NEIGHBORS = 3
SPATIAL_POWER = 2.0

# Frozen Detector Parameters
FROZEN_WINDOW_HOURS = 3
FROZEN_VAR_THRESHOLD = 1e-4

# Drift Detector Parameters (CUSUM & Slope)
DRIFT_WINDOW_HOURS = 12
CUSUM_K = 1.5          # Allowance / deadband (1.5 sigma) to filter out normal warm/cool day variations
CUSUM_H = 10.0         # Decision threshold for sustained drift accumulation
DRIFT_SUSTAINED_HOURS = 8  # Require CUSUM / slope anomaly sustained for >= 8 consecutive hours

# Imputation Engine Parameters
IMPUTATION_CONFIDENCE_THRESHOLD = 0.70  # Only self-heal when ML confidence >= 0.70

