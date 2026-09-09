import os
import joblib
import pandas as pd
import numpy as np
import shap

_clf_model = None
_explainer = None
FEATURE_COLS = ["temporal_score", "spatial_score", "frozen_score", "drift_score", "neighbor_agreement", "hour_of_day", "elevation_m"]
CLASS_NAMES = ["none", "spike", "drift", "frozen", "missing"]

def get_explainer():
    global _clf_model, _explainer
    if _explainer is None:
        model_path = os.path.join(os.path.dirname(__file__), "fault_classifier.joblib")
        if os.path.exists(model_path):
            _clf_model = joblib.load(model_path)
            _explainer = shap.TreeExplainer(_clf_model)
        else:
            raise FileNotFoundError(f"Model file not found at {model_path}")
    return _clf_model, _explainer

def compute_shap_breakdown(feature_dict):
    """
    Computes per-prediction SHAP values for a given feature dictionary.
    Returns ranked dictionary of top feature contributions (%) and summary text.
    """
    try:
        clf, explainer = get_explainer()
        
        # Build single row dataframe
        df = pd.DataFrame([feature_dict])[FEATURE_COLS]
        
        # Predict class index
        pred_class_idx = clf.predict(df)[0]
        
        # Calculate SHAP values
        shap_vals = explainer.shap_values(df)
        
        # Handle multi-class output format (array shape: [1, n_features, n_classes] or list of arrays)
        if isinstance(shap_vals, list):
            # List of arrays per class
            class_shap = shap_vals[pred_class_idx][0]
        elif len(shap_vals.shape) == 3:
            # Shape (1, n_features, n_classes)
            class_shap = shap_vals[0, :, pred_class_idx]
        else:
            class_shap = shap_vals[0]
            
        # Absolute or positive SHAP impact
        impacts = np.maximum(class_shap, 0)
        total_impact = np.sum(impacts)
        
        if total_impact > 0:
            pcts = (impacts / total_impact) * 100.0
        else:
            # Fallback to feature importances if SHAP sum is zero
            pcts = clf.feature_importances_ * 100.0
            
        feat_pcts = {col: round(float(pct), 1) for col, pct in zip(FEATURE_COLS, pcts)}
        
        # Sort features by contribution descending
        sorted_feats = dict(sorted(feat_pcts.items(), key=lambda item: item[1], reverse=True))
        
        # Top 3 features
        top_3 = list(sorted_feats.items())[:3]
        summary_items = [f"{feat}: {pct}%" for feat, pct in top_3 if pct > 0]
        summary_str = f"Primary SHAP drivers: {', '.join(summary_items)}" if summary_items else "SHAP attribution uniform."
        
        return {
            "predicted_class": CLASS_NAMES[pred_class_idx],
            "feature_contributions": sorted_feats,
            "top_drivers": summary_str
        }
    except Exception as e:
        return {
            "predicted_class": "unknown",
            "feature_contributions": {col: 0.0 for col in FEATURE_COLS},
            "top_drivers": f"SHAP calculation error: {str(e)}"
        }

if __name__ == "__main__":
    test_sample = {
        "temporal_score": 0.38,
        "spatial_score": 4.30,
        "frozen_score": 0.00,
        "drift_score": 0.46,
        "neighbor_agreement": 1.0,
        "hour_of_day": 8,
        "elevation_m": 560.0
    }
    res = compute_shap_breakdown(test_sample)
    print("Test Sample SHAP Result:")
    print(res)
