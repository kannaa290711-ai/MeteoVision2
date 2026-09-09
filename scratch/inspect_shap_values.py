import os
import sys
import joblib
import pandas as pd
import numpy as np
import shap

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../analysis-engine")))

model_path = os.path.join(os.path.dirname(__file__), "../analysis-engine/fault_classifier.joblib")
clf = joblib.load(model_path)
explainer = shap.TreeExplainer(clf)

feature_cols = clf.feature_names_in_
class_names = ["none", "spike", "drift", "frozen", "missing"]

# Flag #6849 values:
sample_dict = {
    "temporal_score": 0.38,
    "spatial_score": 4.30,
    "frozen_score": 0.00,
    "drift_score": 0.46,
    "neighbor_agreement": 1.0,
    "hour_of_day": 8,
    "elevation_m": 560.0
}

df_sample = pd.DataFrame([sample_dict])[feature_cols]
pred_class_idx = clf.predict(df_sample)[0]
proba = clf.predict_proba(df_sample)[0]

print("Predicted class:", pred_class_idx, f"({class_names[pred_class_idx]})")
print("Class probabilities:", dict(zip(class_names, proba)))
print("Explainer base values (expected_value):", explainer.expected_value)

shap_vals = explainer.shap_values(df_sample)
print("\nSHAP shape:", np.array(shap_vals).shape)

print("\nSHAP Values breakdown per class for Flag #6849:")
print("-" * 70)
for c_idx, c_name in enumerate(class_names):
    if isinstance(shap_vals, list):
        s_vec = shap_vals[c_idx][0]
    elif len(shap_vals.shape) == 3:
        s_vec = shap_vals[0, :, c_idx]
    else:
        s_vec = shap_vals[0]
        
    print(f"\nClass {c_idx} [{c_name.upper()}] (Predicted Prob: {proba[c_idx]*100:.1f}%):")
    base_val = explainer.expected_value[c_idx] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
    print(f"  Base value (prior prob): {base_val:.4f}")
    sum_shap = np.sum(s_vec)
    print(f"  Sum of SHAP values: {sum_shap:.4f} -> Approx logit/prob shift: {base_val + sum_shap:.4f}")
    
    for f_name, val in zip(feature_cols, s_vec):
        f_val = sample_dict[f_name]
        print(f"    {f_name:20s} (val={f_val:6.2f}) : SHAP = {val:+.6f}")

print("-" * 70)
