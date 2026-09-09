from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict

class SensorHealthScoreSchema(BaseModel):
    id: int
    station_id: str
    variable: str
    health_score: float
    status_tier: str
    fault_count_30d: int
    recency_days: Optional[float] = None
    maintenance_recommendation: str
    last_updated: datetime

    class Config:
        from_attributes = True


class StationSchema(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    elevation_m: float
    status: str = "NORMAL"
    health_score: float = 100.0
    status_tier: str = "Healthy"
    maintenance_recommendation: str = "Routine scheduled maintenance only."
    last_updated: Optional[datetime] = None
    latest_temperature: Optional[float] = None
    latest_humidity: Optional[float] = None
    latest_pressure: Optional[float] = None

    class Config:
        from_attributes = True


class ReadingHistorySchema(BaseModel):
    id: int
    station_id: str
    timestamp: datetime
    # Raw values
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    # AI-Estimated/Imputed values
    temperature_estimated: Optional[float] = None
    humidity_estimated: Optional[float] = None
    pressure_estimated: Optional[float] = None
    # Imputation confidence
    temp_imputed_conf: Optional[float] = None
    humidity_imputed_conf: Optional[float] = None
    pressure_imputed_conf: Optional[float] = None
    # Status labels
    temp_status_label: str = "Raw / Verified"
    humidity_status_label: str = "Raw / Verified"
    pressure_status_label: str = "Raw / Verified"
    # Flagged statuses
    temp_flagged: bool = False
    humidity_flagged: bool = False
    pressure_flagged: bool = False
    # Predicted fault types
    temp_fault_type: str = "none"
    humidity_fault_type: str = "none"
    pressure_fault_type: str = "none"
    max_score: float = 0.0


class AlertSchema(BaseModel):
    id: int
    station_id: str
    station_name: str
    variable: str
    timestamp: datetime
    temporal_score: float
    spatial_score: float
    frozen_score: float = 0.0
    drift_score: float = 0.0
    neighbor_agreement: float = 1.0
    combined_score: float
    flagged: bool
    predicted_fault_type: str = "none"
    ml_confidence: float = 0.0
    explanation_text: Optional[str] = None
    estimated_value: Optional[float] = None
    imputation_method: Optional[str] = None
    imputation_confidence: Optional[float] = None
    physics_check_passed: Optional[bool] = None
    status_label: str = "Flagged — Under Review"
    # SHAP Explainability additions
    shap_contributions: Optional[Dict[str, float]] = None
    shap_summary: Optional[str] = None
    # Multivariate consistency score
    multivariate_consistency_score: Optional[float] = None


class LineageRecordSchema(BaseModel):
    flag_id: int
    reading_id: Optional[int]
    station_id: str
    station_name: str
    variable: str
    timestamp: datetime
    raw_value: Optional[float]
    temporal_score: float
    spatial_score: float
    frozen_score: float
    drift_score: float
    neighbor_agreement: float
    predicted_fault_type: str
    ml_confidence: float
    estimated_value: Optional[float]
    imputation_method: Optional[str]
    spatial_estimate: Optional[float]
    temporal_estimate: Optional[float]
    imputation_confidence: Optional[float]
    physics_check_passed: Optional[bool]
    physics_check_details: Optional[str]
    status_label: str
    xai_explanation: Optional[str]
    # SHAP Explainability & Multivariate additions
    shap_contributions: Optional[Dict[str, float]] = None
    shap_summary: Optional[str] = None
    multivariate_consistency_score: Optional[float] = None


class EvaluationMetricsSchema(BaseModel):
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int
    variable_metrics: Dict[str, Dict[str, float]]
    fault_type_recall: Dict[str, float]
