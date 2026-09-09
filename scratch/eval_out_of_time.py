import sys
import os
import pandas as pd
import numpy as np
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, AnomalyFlag, GroundTruthFault
from sklearn.metrics import classification_report, confusion_matrix

LABEL_MAP = {"none": 0, "spike": 1, "drift": 2, "frozen": 3, "missing": 4}
INV_LABEL_MAP = {0: "none", 1: "spike", 2: "drift", 3: "frozen", 4: "missing"}

db = SessionLocal()
try:
    print("=" * 65)
    print("PART 1 — OUT-OF-TIME TEST SET EVALUATION (30% Split, 46,656 rows)")
    print("=" * 65)

    stations = db.query(Station).all()
    meta_df = pd.DataFrame([{
        "station_id": s.station_id, "elevation_m": s.elevation_m
    } for s in stations]).set_index("station_id")

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

    min_ts = flags_df["timestamp"].min()
    max_ts = flags_df["timestamp"].max()
    split_ts = min_ts + pd.Timedelta(seconds=(max_ts - min_ts).total_seconds() * 0.70)

    test_df = flags_df[flags_df["timestamp"] > split_ts]

    feature_cols = ["temporal_score", "spatial_score", "frozen_score", "drift_score", "neighbor_agreement", "hour_of_day", "elevation_m"]
    X_test = test_df[feature_cols]
    y_test = test_df["target_class"]

    model_path = os.path.join(os.path.dirname(__file__), "../analysis-engine/fault_classifier.joblib")
    clf = joblib.load(model_path)

    y_pred = clf.predict(X_test)

    class_names = ["none", "spike", "drift", "frozen", "missing"]
    report = classification_report(y_test, y_pred, target_names=class_names, digits=4, output_dict=True)

    macro_f1 = np.mean([report[c]["f1-score"] for c in class_names])
    weighted_f1 = report["weighted avg"]["f1-score"]

    print(f"Test Set Size: {len(y_test)} rows (from {split_ts.strftime('%Y-%m-%d %H:%M')} to {max_ts.strftime('%Y-%m-%d %H:%M')})")
    print("-" * 65)
    print(f"{'Class':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 65)
    for c in class_names:
        m = report[c]
        print(f"{c.capitalize():<12} | {m['precision']*100:9.2f}% | {m['recall']*100:9.2f}% | {m['f1-score']*100:9.2f}% | {int(m['support']):8d}")
    print("-" * 65)
    print(f"{'MACRO AVG':<12} | {'-':<10} | {'-':<10} | {macro_f1*100:9.2f}% | {len(y_test):8d}")
    print(f"{'WEIGHTED AVG':<12} | {'-':<10} | {'-':<10} | {weighted_f1*100:9.2f}% | {len(y_test):8d}")
    print("=" * 65)

finally:
    db.close()
