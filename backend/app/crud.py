import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from .models import Station, RawReading, AnomalyFlag, GroundTruthFault, ImputedReading, SensorHealthScore, XAINarrative

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../analysis-engine")))
from shap_explainer import compute_shap_breakdown
from multivariate_analyzer import compute_multivariate_consistency

def get_all_stations_with_status(db: Session):
    stations = db.query(Station).all()
    results = []
    
    latest_ts = db.query(func.max(RawReading.timestamp)).scalar()
    
    for st in stations:
        latest_rd = db.query(RawReading).filter(
            RawReading.station_id == st.station_id
        ).order_by(desc(RawReading.timestamp)).first()
        
        active_flags = 0
        if latest_ts:
            cutoff = latest_ts - timedelta(hours=24)
            active_flags = db.query(AnomalyFlag).filter(
                AnomalyFlag.station_id == st.station_id,
                AnomalyFlag.timestamp >= cutoff,
                AnomalyFlag.flagged == True,
                AnomalyFlag.predicted_fault_type != "none"
            ).count()
            
        status = "ANOMALY" if active_flags > 0 else "NORMAL"
        
        # Query Health Score for overall station
        health_rec = db.query(SensorHealthScore).filter(
            SensorHealthScore.station_id == st.station_id,
            SensorHealthScore.variable == "overall"
        ).first()
        
        h_score = health_rec.health_score if health_rec else 100.0
        h_tier = health_rec.status_tier if health_rec else "Healthy"
        h_rec = health_rec.maintenance_recommendation if health_rec else "Routine scheduled maintenance only."
        
        results.append({
            "station_id": st.station_id,
            "name": st.name,
            "lat": st.lat,
            "lon": st.lon,
            "elevation_m": st.elevation_m,
            "status": status,
            "health_score": h_score,
            "status_tier": h_tier,
            "maintenance_recommendation": h_rec,
            "last_updated": latest_rd.timestamp if latest_rd else None,
            "latest_temperature": latest_rd.temperature if latest_rd else None,
            "latest_humidity": latest_rd.humidity if latest_rd else None,
            "latest_pressure": latest_rd.pressure if latest_rd else None
        })
        
    return results


def get_station_history(db: Session, station_id: str, days: int = 7):
    latest_ts = db.query(func.max(RawReading.timestamp)).scalar()
    if not latest_ts:
        return []
        
    start_ts = latest_ts - timedelta(days=days)
    
    readings = db.query(RawReading).filter(
        RawReading.station_id == station_id,
        RawReading.timestamp >= start_ts
    ).order_by(RawReading.timestamp).all()
    
    flags = db.query(AnomalyFlag).filter(
        AnomalyFlag.station_id == station_id,
        AnomalyFlag.timestamp >= start_ts
    ).all()
    
    imputed = db.query(ImputedReading).filter(
        ImputedReading.station_id == station_id,
        ImputedReading.timestamp >= start_ts
    ).all()
    
    flag_map = {(f.timestamp, f.variable): f for f in flags}
    imputed_map = {(imp.timestamp, imp.variable): imp for imp in imputed}
    
    history = []
    for r in readings:
        temp_f = flag_map.get((r.timestamp, "temperature"))
        hum_f = flag_map.get((r.timestamp, "humidity"))
        pres_f = flag_map.get((r.timestamp, "pressure"))
        
        temp_imp = imputed_map.get((r.timestamp, "temperature"))
        hum_imp = imputed_map.get((r.timestamp, "humidity"))
        pres_imp = imputed_map.get((r.timestamp, "pressure"))
        
        scores = [
            temp_f.combined_score if temp_f else 0.0,
            hum_f.combined_score if hum_f else 0.0,
            pres_f.combined_score if pres_f else 0.0,
        ]
        
        history.append({
            "id": r.id,
            "station_id": r.station_id,
            "timestamp": r.timestamp,
            # Raw telemetry
            "temperature": r.temperature,
            "humidity": r.humidity,
            "pressure": r.pressure,
            # AI-Healed / Imputed telemetry
            "temperature_estimated": temp_imp.estimated_value if temp_imp else r.temperature,
            "humidity_estimated": hum_imp.estimated_value if hum_imp else r.humidity,
            "pressure_estimated": pres_imp.estimated_value if pres_imp else r.pressure,
            # Imputation confidence
            "temp_imputed_conf": temp_imp.imputation_confidence if temp_imp else None,
            "humidity_imputed_conf": hum_imp.imputation_confidence if hum_imp else None,
            "pressure_imputed_conf": pres_imp.imputation_confidence if pres_imp else None,
            # Status labels
            "temp_status_label": temp_imp.status_label if temp_imp else ("Flagged — Under Review" if (temp_f and temp_f.flagged) else "Raw / Verified"),
            "humidity_status_label": hum_imp.status_label if hum_imp else ("Flagged — Under Review" if (hum_f and hum_f.flagged) else "Raw / Verified"),
            "pressure_status_label": pres_imp.status_label if pres_imp else ("Flagged — Under Review" if (pres_f and pres_f.flagged) else "Raw / Verified"),
            # Flagged statuses & fault types
            "temp_flagged": temp_f.flagged if temp_f else False,
            "humidity_flagged": hum_f.flagged if hum_f else False,
            "pressure_flagged": pres_f.flagged if pres_f else False,
            "temp_fault_type": temp_f.predicted_fault_type if temp_f else "none",
            "humidity_fault_type": hum_f.predicted_fault_type if hum_f else "none",
            "pressure_fault_type": pres_f.predicted_fault_type if pres_f else "none",
            "max_score": max(scores) if scores else 0.0
        })
        
    return history


def get_recent_alerts(db: Session, limit: int = 50):
    flags = db.query(AnomalyFlag, Station.name.label("station_name"), Station.elevation_m).join(
        Station, AnomalyFlag.station_id == Station.station_id
    ).filter(
        AnomalyFlag.flagged == True,
        AnomalyFlag.predicted_fault_type != "none"
    ).order_by(desc(AnomalyFlag.timestamp)).limit(limit).all()
    
    alerts = []
    for f, st_name, elev_m in flags:
        narrative = db.query(XAINarrative).filter(XAINarrative.flag_id == f.id).first()
        imputed = db.query(ImputedReading).filter(ImputedReading.flag_id == f.id).first()
        
        # Calculate SHAP breakdown
        feature_dict = {
            "temporal_score": float(f.temporal_score),
            "spatial_score": float(f.spatial_score),
            "frozen_score": float(getattr(f, "frozen_score", 0.0)),
            "drift_score": float(getattr(f, "drift_score", 0.0)),
            "neighbor_agreement": float(getattr(f, "neighbor_agreement", 1.0)),
            "hour_of_day": int(f.timestamp.hour),
            "elevation_m": float(elev_m or 500.0)
        }
        shap_res = compute_shap_breakdown(feature_dict)
        
        # Calculate Multivariate Consistency Score
        mv_score, _ = compute_multivariate_consistency(db, f.station_id, f.timestamp, f.variable, f.combined_score)
        
        alerts.append({
            "id": f.id,
            "station_id": f.station_id,
            "station_name": st_name,
            "variable": f.variable,
            "timestamp": f.timestamp,
            "temporal_score": f.temporal_score,
            "spatial_score": f.spatial_score,
            "frozen_score": getattr(f, "frozen_score", 0.0),
            "drift_score": getattr(f, "drift_score", 0.0),
            "neighbor_agreement": getattr(f, "neighbor_agreement", 1.0),
            "combined_score": f.combined_score,
            "flagged": f.flagged,
            "predicted_fault_type": f.predicted_fault_type,
            "ml_confidence": f.ml_confidence,
            "explanation_text": narrative.explanation_text if narrative else None,
            "estimated_value": imputed.estimated_value if imputed else None,
            "imputation_method": imputed.imputation_method if imputed else None,
            "imputation_confidence": imputed.imputation_confidence if imputed else None,
            "physics_check_passed": imputed.physics_check_passed if imputed else None,
            "status_label": imputed.status_label if imputed else "Flagged — Under Review",
            # SHAP & Multivariate additions
            "shap_contributions": shap_res["feature_contributions"],
            "shap_summary": shap_res["top_drivers"],
            "multivariate_consistency_score": mv_score
        })
    return alerts


def get_data_lineage(db: Session, flag_id: int):
    flag = db.query(AnomalyFlag).filter(AnomalyFlag.id == flag_id).first()
    if not flag:
        return None
        
    st = db.query(Station).filter(Station.station_id == flag.station_id).first()
    st_name = st.name if st else flag.station_id
    elev_m = st.elevation_m if st else 500.0
    
    reading = db.query(RawReading).filter(RawReading.id == flag.reading_id).first() if flag.reading_id else None
    raw_val = getattr(reading, flag.variable, None) if reading else None
    
    imputed = db.query(ImputedReading).filter(ImputedReading.flag_id == flag_id).first()
    narrative = db.query(XAINarrative).filter(XAINarrative.flag_id == flag_id).first()
    
    # Calculate SHAP breakdown & Multivariate consistency
    feature_dict = {
        "temporal_score": float(flag.temporal_score),
        "spatial_score": float(flag.spatial_score),
        "frozen_score": float(getattr(flag, "frozen_score", 0.0)),
        "drift_score": float(getattr(flag, "drift_score", 0.0)),
        "neighbor_agreement": float(getattr(flag, "neighbor_agreement", 1.0)),
        "hour_of_day": int(flag.timestamp.hour),
        "elevation_m": float(elev_m)
    }
    shap_res = compute_shap_breakdown(feature_dict)
    mv_score, mv_clause = compute_multivariate_consistency(db, flag.station_id, flag.timestamp, flag.variable, flag.combined_score)
    
    # Combine explanation with multivariate clause
    base_explanation = narrative.explanation_text if narrative else ""
    full_explanation = f"{base_explanation} {mv_clause}".strip()
    
    return {
        "flag_id": flag.id,
        "reading_id": flag.reading_id,
        "station_id": flag.station_id,
        "station_name": st_name,
        "variable": flag.variable,
        "timestamp": flag.timestamp,
        "raw_value": raw_val,
        "temporal_score": flag.temporal_score,
        "spatial_score": flag.spatial_score,
        "frozen_score": getattr(flag, "frozen_score", 0.0),
        "drift_score": getattr(flag, "drift_score", 0.0),
        "neighbor_agreement": getattr(flag, "neighbor_agreement", 1.0),
        "predicted_fault_type": flag.predicted_fault_type,
        "ml_confidence": flag.ml_confidence,
        "estimated_value": imputed.estimated_value if imputed else None,
        "imputation_method": imputed.imputation_method if imputed else None,
        "spatial_estimate": imputed.spatial_estimate if imputed else None,
        "temporal_estimate": imputed.temporal_estimate if imputed else None,
        "imputation_confidence": imputed.imputation_confidence if imputed else None,
        "physics_check_passed": imputed.physics_check_passed if imputed else None,
        "physics_check_details": imputed.physics_check_details if imputed else None,
        "status_label": imputed.status_label if imputed else ("Flagged — Under Review" if flag.flagged else "Raw / Verified"),
        "xai_explanation": full_explanation,
        "shap_contributions": shap_res["feature_contributions"],
        "shap_summary": shap_res["top_drivers"],
        "multivariate_consistency_score": mv_score
    }


def get_sensor_health_details(db: Session, station_id: str):
    scores = db.query(SensorHealthScore).filter(SensorHealthScore.station_id == station_id).all()
    return [
        {
            "id": s.id,
            "station_id": s.station_id,
            "variable": s.variable,
            "health_score": s.health_score,
            "status_tier": s.status_tier,
            "fault_count_30d": s.fault_count_30d,
            "recency_days": s.recency_days,
            "maintenance_recommendation": s.maintenance_recommendation,
            "last_updated": s.last_updated
        }
        for s in scores
    ]


from predictive_degradation import compute_predictive_degradation

def get_predictive_health_forecast(db: Session, station_id: str):
    """Return RUL (Remaining Useful Life) and health score decay forecast (+7d, +14d, +30d) per variable."""
    return compute_predictive_degradation(station_id, db=db)


def get_edge_node_status(station_id: str):
    """Return simulated ESP32 Edge-AI microcontroller status, RAM/flash footprint, and sub-ms latency metrics."""
    return {
        "station_id": station_id,
        "firmware_version": "v2.1-ESP32-EdgeAI",
        "architecture": "Xtensa LX6 (Dual-Core @ 240MHz)",
        "edge_inference_latency_ms": 0.022,
        "ram_usage_kb": 18.4,
        "flash_usage_kb": 64.2,
        "bandwidth_saving_pct": 71.4,
        "edge_self_healing_active": True,
        "status": "ONLINE"
    }


from satellite_verifier import verify_with_insat3d
from technician_dispatch import generate_technician_work_orders

def get_satellite_verification(db: Session, station_id: str, combined_score: float = 0.0):
    """Return ISRO INSAT-3D / 3DR satellite cross-validation results for ground station."""
    return verify_with_insat3d(station_id, combined_score=combined_score, db=db)


def get_technician_work_orders(db: Session):
    """Return structured JSON / SMS field technician dispatch maintenance work orders for degraded stations."""
    return generate_technician_work_orders(db=db)


