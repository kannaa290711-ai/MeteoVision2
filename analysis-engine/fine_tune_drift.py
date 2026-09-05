import sys
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, AnomalyFlag, GroundTruthFault

LABEL_MAP = {"none": 0, "spike": 1, "drift": 2, "frozen": 3, "missing": 4}
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
    
    print(f"{'Drift Weight':<12} | {'Drift P':<9} | {'Drift R':<9} | {'Drift F1':<9} | {'Macro F1':<9} | {'Weighted F1':<11} | {'FP (None->Drift)':<16}")
    print("-" * 90)
    
    for dw in [10.0, 12.0, 14.0, 15.0, 16.0, 18.0]:
        cw = {0: 1.0, 1: 50.0, 2: dw, 3: 30.0, 4: 40.0}
        clf = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, class_weight=cw, n_jobs=-1)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        
        rep = classification_report(y_test, y_pred, target_names=CLASS_NAMES, digits=4, output_dict=True)
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3, 4])
        
        macro_f1 = np.mean([rep[c]["f1-score"] for c in CLASS_NAMES])
        weighted_f1 = rep["weighted avg"]["f1-score"]
        fp_none_drift = cm[0, 2]
        
        print(f"{dw:<12.1f} | {rep['drift']['precision']*100:8.2f}% | {rep['drift']['recall']*100:8.2f}% | {rep['drift']['f1-score']*100:8.2f}% | {macro_f1*100:8.2f}% | {weighted_f1*100:10.2f}% | {fp_none_drift:<16d}")

if __name__ == "__main__":
    main()
