import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import AnomalyFlag, GroundTruthFault

def evaluate_detection_performance():
    print("=" * 60)
    print("  AETHERIX SENTINEL - Evaluation & Metrics Engine")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Load anomaly flags
        flags_query = db.query(AnomalyFlag).all()
        flags_df = pd.DataFrame([
            {
                "id": f.id,
                "station_id": f.station_id,
                "variable": f.variable,
                "timestamp": f.timestamp,
                "flagged": f.flagged,
                "combined_score": f.combined_score
            }
            for f in flags_query
        ])
        
        # Load ground truth faults
        faults_query = db.query(GroundTruthFault).all()
        faults_df = pd.DataFrame([
            {
                "station_id": g.station_id,
                "variable": g.variable,
                "fault_type": g.fault_type,
                "start_time": g.start_time,
                "end_time": g.end_time
            }
            for g in faults_query
        ])
        
        if flags_df.empty:
            print("No anomaly flags found. Run detector_pipeline.py first.")
            return {}
            
        print(f"Evaluating {len(flags_df)} anomaly flag records against {len(faults_df)} ground-truth fault intervals...")
        
        # Determine ground truth status for every flagged reading
        flags_df["is_ground_truth"] = False
        flags_df["ground_truth_fault_type"] = None
        
        # Group ground truth by (station_id, variable) for fast lookup
        fault_groups = faults_df.groupby(["station_id", "variable"])
        
        for (st_id, var), group in fault_groups:
            mask = (flags_df["station_id"] == st_id) & (flags_df["variable"] == var)
            sub_df = flags_df[mask]
            
            for _, fault in group.iterrows():
                time_mask = mask & (flags_df["timestamp"] >= fault["start_time"]) & (flags_df["timestamp"] <= fault["end_time"])
                flags_df.loc[time_mask, "is_ground_truth"] = True
                flags_df.loc[time_mask, "ground_truth_fault_type"] = fault["fault_type"]
                
        # Overall Confusion Matrix
        tp = int(((flags_df["flagged"] == True) & (flags_df["is_ground_truth"] == True)).sum())
        fp = int(((flags_df["flagged"] == True) & (flags_df["is_ground_truth"] == False)).sum())
        fn = int(((flags_df["flagged"] == False) & (flags_df["is_ground_truth"] == True)).sum())
        tn = int(((flags_df["flagged"] == False) & (flags_df["is_ground_truth"] == False)).sum())
        
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
        
        print("\n" + "=" * 60)
        print("  OVERALL PERFORMANCE METRICS")
        print("=" * 60)
        print(f"  True Positives  (TP): {tp:6d}  |  False Positives (FP): {fp:6d}")
        print(f"  False Negatives (FN): {fn:6d}  |  True Negatives  (TN): {tn:6d}")
        print("-" * 60)
        print(f"  PRECISION:  {precision * 100:.2f}%")
        print(f"  RECALL:     {recall * 100:.2f}%")
        print(f"  F1 SCORE:   {f1 * 100:.2f}%")
        print("=" * 60)
        
        # Metrics by Variable
        var_metrics = {}
        print("\nMetrics by Variable:")
        for var in ["temperature", "humidity", "pressure"]:
            v_df = flags_df[flags_df["variable"] == var]
            v_tp = int(((v_df["flagged"] == True) & (v_df["is_ground_truth"] == True)).sum())
            v_fp = int(((v_df["flagged"] == True) & (v_df["is_ground_truth"] == False)).sum())
            v_fn = int(((v_df["flagged"] == False) & (v_df["is_ground_truth"] == True)).sum())
            
            v_prec = round(v_tp / (v_tp + v_fp), 4) if (v_tp + v_fp) > 0 else 0.0
            v_rec = round(v_tp / (v_tp + v_fn), 4) if (v_tp + v_fn) > 0 else 0.0
            v_f1 = round(2 * (v_prec * v_rec) / (v_prec + v_rec), 4) if (v_prec + v_rec) > 0 else 0.0
            
            var_metrics[var] = {"precision": v_prec, "recall": v_rec, "f1": v_f1}
            print(f"  - {var.capitalize():12s}: Precision={v_prec*100:5.1f}%, Recall={v_rec*100:5.1f}%, F1={v_f1*100:5.1f}%")
            
        # Metrics by Fault Type
        fault_type_metrics = {}
        print("\nRecall by Fault Type:")
        for ftype in ["spike", "drift", "frozen", "missing"]:
            ft_df = flags_df[flags_df["ground_truth_fault_type"] == ftype]
            if not ft_df.empty:
                ft_tp = int((ft_df["flagged"] == True).sum())
                ft_total = len(ft_df)
                ft_rec = round(ft_tp / ft_total, 4)
                fault_type_metrics[ftype] = ft_rec
                print(f"  - {ftype.capitalize():12s}: Detected {ft_tp}/{ft_total} points (Recall={ft_rec*100:5.1f}%)")
                
        print("=" * 60 + "\n")
        
        return {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "variable_metrics": var_metrics,
            "fault_type_recall": fault_type_metrics
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    evaluate_detection_performance()
