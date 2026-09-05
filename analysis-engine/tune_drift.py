import sys
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, AnomalyFlag, GroundTruthFault

LABEL_MAP = {"none": 0, "spike": 1, "drift": 2, "frozen": 3, "missing": 4}
INV_LABEL_MAP = {0: "none", 1: "spike", 2: "drift", 3: "frozen", 4: "missing"}
CLASS_NAMES = ["none", "spike", "drift", "frozen", "missing"]

def load_data():
    db = SessionLocal()
    try:
        stations = db.query(Station).all()
        meta_df = pd.DataFrame([{"station_id": s.station_id, "elevation_m": s.elevation_m} for s in stations]).set_index("station_id")
        
        flags_df = pd.DataFrame([{
            "id": f.id,
            "station_id": f.station_id,
            "variable": f.variable,
            "timestamp": f.timestamp,
            "temporal_score": f.temporal_score,
            "spatial_score": f.spatial_score,
            "frozen_score": getattr(f, "frozen_score", 0.0),
            "drift_score": getattr(f, "drift_score", 0.0),
            "neighbor_agreement": getattr(f, "neighbor_agreement", 1.0),
            "hour_of_day": f.timestamp.hour
        } for f in db.query(AnomalyFlag).all()])
        
        flags_df["elevation_m"] = flags_df["station_id"].apply(lambda s: meta_df.loc[s, "elevation_m"] if s in meta_df.index else 500.0)
        
        faults_df = pd.DataFrame([{
            "station_id": g.station_id,
            "variable": g.variable,
            "fault_type": g.fault_type,
            "start_time": g.start_time,
            "end_time": g.end_time
        } for g in db.query(GroundTruthFault).all()])
        
        flags_df["target_label"] = "none"
        fault_groups = faults_df.groupby(["station_id", "variable"])
        for (st_id, var), group in fault_groups:
            mask = (flags_df["station_id"] == st_id) & (flags_df["variable"] == var)
            for _, fault in group.iterrows():
                time_mask = mask & (flags_df["timestamp"] >= fault["start_time"]) & (flags_df["timestamp"] <= fault["end_time"])
                flags_df.loc[time_mask, "target_label"] = fault["fault_type"]
                
        flags_df["target_class"] = flags_df["target_label"].map(LABEL_MAP)
        return flags_df
    finally:
        db.close()

def evaluate_predictions(y_test, y_pred, title=""):
    rep = classification_report(y_test, y_pred, target_names=CLASS_NAMES, digits=4, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3, 4])
    
    # Calculate Macro F1 & Weighted F1
    macro_f1 = np.mean([rep[c]["f1-score"] for c in CLASS_NAMES])
    weighted_f1 = rep["weighted avg"]["f1-score"]
    
    drift_p = rep["drift"]["precision"]
    drift_r = rep["drift"]["recall"]
    drift_f1 = rep["drift"]["f1-score"]
    
    print(f"\n--- {title} ---")
    print(f"Drift Precision: {drift_p*100:.2f}% | Drift Recall: {drift_r*100:.2f}% | Drift F1: {drift_f1*100:.2f}%")
    print(f"Macro F1: {macro_f1*100:.2f}% | Weighted F1: {weighted_f1*100:.2f}%")
    print("Other Classes Precision / Recall / F1:")
    for c in ["missing", "frozen", "spike", "none"]:
        print(f"  - {c.capitalize():<8}: P={rep[c]['precision']*100:.2f}%, R={rep[c]['recall']*100:.2f}%, F1={rep[c]['f1-score']*100:.2f}%")
    
    cm_df = pd.DataFrame(cm, index=[c.capitalize() for c in CLASS_NAMES], columns=[c.capitalize() for c in CLASS_NAMES])
    print("\nConfusion Matrix:")
    print(cm_df.to_string())
    return rep, cm_df, macro_f1, weighted_f1

def main():
    flags_df = load_data()
    
    min_ts = flags_df["timestamp"].min()
    max_ts = flags_df["timestamp"].max()
    split_ts = min_ts + pd.Timedelta(seconds=(max_ts - min_ts).total_seconds() * 0.70)
    
    train_df = flags_df[flags_df["timestamp"] <= split_ts]
    test_df = flags_df[flags_df["timestamp"] > split_ts]
    
    feature_cols = ["temporal_score", "spatial_score", "frozen_score", "drift_score", "neighbor_agreement", "hour_of_day", "elevation_m"]
    X_train = train_df[feature_cols]
    y_train = train_df["target_class"]
    X_test = test_df[feature_cols]
    y_test = test_df["target_class"]
    
    # -------------------------------------------------------------
    # 1. Baseline Model (balanced class_weight, standard argmax)
    # -------------------------------------------------------------
    print("Training Baseline Model (class_weight='balanced')...")
    clf_base = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, class_weight="balanced", n_jobs=-1)
    clf_base.fit(X_train, y_train)
    y_probs_base = clf_base.predict_proba(X_test)
    y_pred_base = clf_base.predict(X_test)
    
    evaluate_predictions(y_test, y_pred_base, title="BASELINE (Argmax, class_weight='balanced')")
    
    # -------------------------------------------------------------
    # Approach 1: Threshold Tuning on P(drift)
    # -------------------------------------------------------------
    print("\n" + "="*60)
    print("APPROACH 1: DRIFT PROBABILITY THRESHOLD TUNING")
    print("="*60)
    
    for t_drift in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
        y_pred_custom = np.zeros(len(X_test), dtype=int)
        for i in range(len(X_test)):
            p = y_probs_base[i]
            # p indices: 0:none, 1:spike, 2:drift, 3:frozen, 4:missing
            
            if p[4] > 0.4: # missing
                y_pred_custom[i] = 4
            elif p[3] > 0.4: # frozen
                y_pred_custom[i] = 3
            elif p[1] > 0.4: # spike
                y_pred_custom[i] = 1
            elif p[2] >= t_drift: # drift threshold requirement
                y_pred_custom[i] = 2
            else:
                p_no_drift = p.copy()
                p_no_drift[2] = -1
                y_pred_custom[i] = np.argmax(p_no_drift)
                
        rep, cm_df, macro_f1, weighted_f1 = evaluate_predictions(y_test, y_pred_custom, title=f"Threshold Tuning: P(drift) >= {t_drift:.2f}")

    # -------------------------------------------------------------
    # Approach 2: Adjusted Class Weights
    # -------------------------------------------------------------
    print("\n" + "="*60)
    print("APPROACH 2: RETRAINING WITH ADJUSTED CLASS WEIGHTS")
    print("="*60)
    
    custom_weights_list = [
        {0: 1.0, 1: 50.0, 2: 12.0, 3: 30.0, 4: 40.0},
        {0: 1.0, 1: 50.0, 2: 18.0, 3: 30.0, 4: 40.0},
        {0: 1.0, 1: 50.0, 2: 25.0, 3: 30.0, 4: 40.0},
    ]
    
    for cw in custom_weights_list:
        print(f"\nTesting Custom Class Weight: {cw}")
        clf_cw = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, class_weight=cw, n_jobs=-1)
        clf_cw.fit(X_train, y_train)
        y_pred_cw = clf_cw.predict(X_test)
        evaluate_predictions(y_test, y_pred_cw, title=f"Custom Class Weight: drift_weight={cw[2]}")

if __name__ == "__main__":
    main()
