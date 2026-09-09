import os
import sys
import joblib
import pandas as pd
import numpy as np
import shap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../analysis-engine")))

model_path = os.path.join(os.path.dirname(__file__), "../analysis-engine/fault_classifier.joblib")
clf = joblib.load(model_path)

print("=" * 70)
print("AUDIT PART 1 — MODEL FEATURE NAMES & CLASS LABELS")
print("=" * 70)

print("clf.feature_names_in_:", getattr(clf, "feature_names_in_", "NOT FOUND"))
print("clf.classes_          :", getattr(clf, "classes_", "NOT FOUND"))
print("clf.n_features_in_    :", getattr(clf, "n_features_in_", "NOT FOUND"))

from shap_explainer import FEATURE_COLS, CLASS_NAMES
print("\nFEATURE_COLS in shap_explainer.py:", FEATURE_COLS)
print("CLASS_NAMES in shap_explainer.py :", CLASS_NAMES)

print("\nFeature names order check:")
if hasattr(clf, "feature_names_in_"):
    for idx, (m_feat, s_feat) in enumerate(zip(clf.feature_names_in_, FEATURE_COLS)):
        match = (m_feat == s_feat)
        print(f"  Pos {idx}: Model='{m_feat}' vs Defined='{s_feat}' -> Match: {match}")

print("=" * 70)
print("AUDIT FLAG #6849 EXPLICIT BREAKDOWN")
print("=" * 70)

# Flag #6849 feature values from database
# Flag ID 6849: Spike fault, TS 2026-06-14 08:00:00, temporal_score=0.38, spatial_score=4.30, frozen_score=0.0, drift_score=0.46, neighbor_agreement=1.0, hour=8, elevation=560.0
sample_dict = {
    "temporal_score": 0.38,
    "spatial_score": 4.30,
    "frozen_score": 0.00,
    "drift_score": 0.46,
    "neighbor_agreement": 1.0,
    "hour_of_day": 8,
    "elevation_m": 560.0
}

df_sample = pd.DataFrame([sample_dict])[clf.feature_names_in_ if hasattr(clf, "feature_names_in_") else FEATURE_COLS]

pred_raw = clf.predict(df_sample)[0]
proba = clf.predict_proba(df_sample)[0]
print("clf.predict() result      :", pred_raw, type(pred_raw))
print("clf.predict_proba() result:", proba)

explainer = shap.TreeExplainer(clf)
shap_vals = explainer.shap_values(df_sample)

print("\nSHAP values type & structure:")
if isinstance(shap_vals, list):
    print(f"  shap_vals is a LIST of length {len(shap_vals)}")
    for i, arr in enumerate(shap_vals):
        print(f"    Class {i} ({clf.classes_[i]}): shape {arr.shape}, values: {arr[0]}")
elif isinstance(shap_vals, np.ndarray):
    print(f"  shap_vals is an ndarray of shape {shap_vals.shape}")
    if len(shap_vals.shape) == 3:
        # shape: (n_samples, n_features, n_classes) or (n_samples, n_classes, n_features)?
        print(f"  3D array shape: {shap_vals.shape}")

print("=" * 70)
