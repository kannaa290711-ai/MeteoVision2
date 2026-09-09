import sys
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../analysis-engine")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.database import get_db, engine, Base
from backend.app.schemas import (
    StationSchema, ReadingHistorySchema, AlertSchema, EvaluationMetricsSchema,
    LineageRecordSchema, SensorHealthScoreSchema, PredictiveHealthSchema, EdgeNodeStatusSchema
)
from backend.app.crud import (
    get_all_stations_with_status, get_station_history, get_recent_alerts,
    get_data_lineage, get_sensor_health_details
)
from evaluate import evaluate_detection_performance

app = FastAPI(
    title="AETHERIX SENTINEL - AWS Anomaly Detection & Self-Healing API",
    description="Phase 3 API for SIH 2026 Problem Statement 26073 - Self-Healing, Health Scoring & XAI Narrative Engine",
    version="3.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "AETHERIX SENTINEL",
        "phase": "Phase 3 Self-Healing & Health Scoring",
        "docs_url": "/docs"
    }


@app.get("/api/stations", response_model=List[StationSchema])
def list_stations(db: Session = Depends(get_db)):
    """Return all 12 AWS stations with active anomaly status, sensor health score, and latest readings."""
    return get_all_stations_with_status(db)


@app.get("/api/stations/{station_id}/history", response_model=List[ReadingHistorySchema])
def get_station_readings_history(station_id: str, days: int = Query(default=7, ge=1, le=180), db: Session = Depends(get_db)):
    """Return historical time-series readings with raw vs AI-estimated values and status labels."""
    history = get_station_history(db, station_id, days=days)
    if not history:
        raise HTTPException(status_code=404, detail="Station not found or no historical data available")
    return history


@app.get("/api/sensor-health/{station_id}", response_model=List[SensorHealthScoreSchema])
def get_station_sensor_health(station_id: str, db: Session = Depends(get_db)):
    """Return sensor health score breakdown (0-100), status tier, and maintenance recommendations per variable."""
    scores = get_sensor_health_details(db, station_id)
    if not scores:
        raise HTTPException(status_code=404, detail="Station not found or no health score data available")
    return scores


@app.get("/api/sensor-health/predictive/{station_id}", response_model=PredictiveHealthSchema)
def get_station_predictive_health(station_id: str, db: Session = Depends(get_db)):
    """Return Remaining Useful Life (RUL) and health score decay forecast (+7d, +14d, +30d) for a station."""
    from backend.app.crud import get_predictive_health_forecast
    return get_predictive_health_forecast(db, station_id)


@app.get("/api/edge/status/{station_id}", response_model=EdgeNodeStatusSchema)
def get_station_edge_status(station_id: str):
    """Return simulated ESP32 Edge-AI microcontroller status, RAM/flash footprint, and sub-ms latency metrics."""
    from backend.app.crud import get_edge_node_status
    return get_edge_node_status(station_id)


@app.get("/api/alerts", response_model=List[AlertSchema])
def list_recent_alerts(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    """Return recent flagged anomaly alerts with XAI explanation narratives and self-healed values."""
    return get_recent_alerts(db, limit=limit)


@app.get("/api/lineage/{flag_id}", response_model=LineageRecordSchema)
def get_anomaly_data_lineage(flag_id: int, db: Session = Depends(get_db)):
    """Return full queryable data lineage: raw value -> detection flags -> ML fault type -> quarantine -> estimated value -> physics check -> XAI narrative."""
    lineage = get_data_lineage(db, flag_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Anomaly flag record not found")
    return lineage


from fastapi.responses import StreamingResponse
import json
import asyncio
from backend.app.models import RawReading, AnomalyFlag, Station

@app.get("/api/stream/telemetry")
async def stream_telemetry(speed_sec: float = Query(default=1.0, ge=0.1, le=10.0), db: Session = Depends(get_db)):
    """Server-Sent Events (SSE) endpoint to stream simulated incoming AWS telemetry readings live with SHAP & multivariate metrics."""
    async def event_generator():
        readings = db.query(RawReading).order_by(RawReading.timestamp.desc()).limit(100).all()
        for rd in reversed(readings):
            st = db.query(Station).filter(Station.station_id == rd.station_id).first()
            flag = db.query(AnomalyFlag).filter(
                AnomalyFlag.station_id == rd.station_id,
                AnomalyFlag.timestamp == rd.timestamp
            ).first()
            
            payload = {
                "station_id": rd.station_id,
                "station_name": st.name if st else rd.station_id,
                "timestamp": rd.timestamp.isoformat(),
                "temperature": rd.temperature,
                "humidity": rd.humidity,
                "pressure": rd.pressure,
                "flagged": flag.flagged if flag else False,
                "fault_type": flag.predicted_fault_type if flag else "none",
                "shap_summary": getattr(flag, "shap_summary", None) if flag else None,
                "multivariate_consistency_score": float(getattr(flag, "multivariate_consistency_score", 1.0)) if flag else 1.0
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(speed_sec)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


_cached_metrics = None

@app.get("/api/metrics/evaluation")
def get_evaluation_metrics():
    """Return live Precision, Recall, F1 score metrics comparing anomaly flags against ground truth (cached for performance)."""
    global _cached_metrics
    if _cached_metrics is None:
        _cached_metrics = evaluate_detection_performance()
    return _cached_metrics

