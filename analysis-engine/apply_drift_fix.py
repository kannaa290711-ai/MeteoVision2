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

def main():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("  AETHERIX SENTINEL - Phase 2 Quick Fix: Drift Precision Calibration")
        print("=" * 60)
        
        # 1. Load data
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
        
        # 2. Time-Based Split (70% Train, 30% Test)
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
        
        # 3. Retrain Classifier with calibrated class weights
        print("\nTraining Calibrated Classifier (class_weight={none:1, spike:50, drift:10, frozen:30, missing:40})...")
        calibrated_cw = {0: 1.0, 1: 50.0, 2: 10.0, 3: 30.0, 4: 40.0}
        clf = RandomForestClassifier(
            n_estimators=120,
            max_depth=12,
            random_state=42,
            class_weight=calibrated_cw,
            n_jobs=-1
        )
        clf.fit(X_train, y_train)
        
        # Save model
        model_path = os.path.join(os.path.dirname(__file__), "fault_classifier.joblib")
        joblib.dump(clf, model_path)
        print(f"      Saved calibrated model to: {model_path}")
        
        # 4. Out-of-Time Test Set Evaluation
        y_pred = clf.predict(X_test)
        y_probs = clf.predict_proba(X_test)
        
        report = classification_report(y_test, y_pred, target_names=CLASS_NAMES, digits=4, output_dict=True)
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3, 4])
        
        macro_f1 = np.mean([report[c]["f1-score"] for c in CLASS_NAMES])
        weighted_f1 = report["weighted avg"]["f1-score"]
        
        print("\n" + "=" * 65)
        print("  CLASSIFICATION PERFORMANCE ON OUT-OF-TIME TEST SET (CALIBRATED)")
        print("=" * 65)
        print(f"{'Class':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
        print("-" * 65)
        for c in CLASS_NAMES:
            m = report[c]
            print(f"{c.capitalize():<12} | {m['precision']*100:9.2f}% | {m['recall']*100:9.2f}% | {m['f1-score']*100:9.2f}% | {int(m['support']):8d}")
        print("-" * 65)
        print(f"{'MACRO AVG':<12} | {'-':<10} | {'-':<10} | {macro_f1*100:9.2f}% | {len(y_test):8d}")
        print(f"{'WEIGHTED AVG':<12} | {'-':<10} | {'-':<10} | {weighted_f1*100:9.2f}% | {len(y_test):8d}")
        print("=" * 65)
        
        print("\nConfusion Matrix (Rows=True, Cols=Predicted):")
        cm_df = pd.DataFrame(cm, index=[c.capitalize() for c in CLASS_NAMES], columns=[c.capitalize() for c in CLASS_NAMES])
        print(cm_df.to_string())
        
        print("\nFeature Importances Ranking:")
        importances = pd.Series(clf.feature_importances_, index=feature_cols).sort_values(ascending=False)
        for feat, imp in importances.items():
            print(f"  - {feat:20s}: {imp*100:5.2f}%")
            
        # 5. Update Database anomaly_flags with predictions
        print("\nUpdating database anomaly_flags with calibrated predictions...")
        all_pred = clf.predict(flags_df[feature_cols])
        all_probs = clf.predict_proba(flags_df[feature_cols])
        
        flags_df["pred_class"] = all_pred
        flags_df["pred_label"] = flags_df["pred_class"].map(INV_LABEL_MAP)
        flags_df["confidence"] = np.max(all_probs, axis=1)
        flags_df["ml_flagged"] = flags_df["pred_label"] != "none"
        
        for idx, row in flags_df.iterrows():
            db.query(AnomalyFlag).filter(AnomalyFlag.id == row["id"]).update({
                "predicted_fault_type": row["pred_label"],
                "ml_confidence": float(row["confidence"]),
                "flagged": bool(row["ml_flagged"])
            })
        db.commit()
        print("      Database updated cleanly!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
