from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Station(Base):
    __tablename__ = "stations"

    station_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)

    readings = relationship("RawReading", back_populates="station", cascade="all, delete-orphan")
    faults = relationship("GroundTruthFault", back_populates="station", cascade="all, delete-orphan")
    flags = relationship("AnomalyFlag", back_populates="station", cascade="all, delete-orphan")


class RawReading(Base):
    __tablename__ = "raw_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)

    station = relationship("Station", back_populates="readings")


class GroundTruthFault(Base):
    __tablename__ = "ground_truth_faults"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    variable = Column(String, nullable=False)  # 'temperature', 'humidity', 'pressure'
    fault_type = Column(String, nullable=False)  # 'spike', 'drift', 'frozen', 'missing'
    start_time = Column(DateTime, index=True, nullable=False)
    end_time = Column(DateTime, index=True, nullable=False)

    station = relationship("Station", back_populates="faults")


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reading_id = Column(Integer, ForeignKey("raw_readings.id"), nullable=True, index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    variable = Column(String, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    temporal_score = Column(Float, nullable=False, default=0.0)
    spatial_score = Column(Float, nullable=False, default=0.0)
    frozen_score = Column(Float, nullable=False, default=0.0)
    drift_score = Column(Float, nullable=False, default=0.0)
    neighbor_agreement = Column(Float, nullable=False, default=0.0)
    combined_score = Column(Float, nullable=False, default=0.0)
    flagged = Column(Boolean, nullable=False, default=False)
    predicted_fault_type = Column(String, nullable=False, default="none")
    ml_confidence = Column(Float, nullable=False, default=0.0)

    station = relationship("Station", back_populates="flags")


class ImputedReading(Base):
    __tablename__ = "imputed_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("anomaly_flags.id"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("raw_readings.id"), nullable=True, index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    variable = Column(String, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    raw_value = Column(Float, nullable=True)
    estimated_value = Column(Float, nullable=False)
    imputation_method = Column(String, nullable=False)
    spatial_estimate = Column(Float, nullable=True)
    temporal_estimate = Column(Float, nullable=True)
    imputation_confidence = Column(Float, nullable=False)
    physics_check_passed = Column(Boolean, nullable=False, default=True)
    physics_check_details = Column(String, nullable=True)
    status_label = Column(String, nullable=False)


class SensorHealthScore(Base):
    __tablename__ = "sensor_health_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    variable = Column(String, nullable=False)  # 'temperature', 'humidity', 'pressure', 'overall'
    health_score = Column(Float, nullable=False, default=100.0)
    status_tier = Column(String, nullable=False, default="Healthy")  # Healthy, Watch, Degraded, Critical
    fault_count_30d = Column(Integer, nullable=False, default=0)
    recency_days = Column(Float, nullable=True)
    maintenance_recommendation = Column(String, nullable=False)
    last_updated = Column(DateTime, index=True, nullable=False)


class XAINarrative(Base):
    __tablename__ = "xai_narratives"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("anomaly_flags.id"), nullable=False, index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True, nullable=False)
    variable = Column(String, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    predicted_fault_type = Column(String, nullable=False)
    explanation_text = Column(String, nullable=False)

