from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="Energy manager")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CampusDB(Base):
    __tablename__ = "campuses"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    tariff_inr_per_kwh = Column(Float, default=8.75)
    grid_carbon_kg_per_kwh = Column(Float, default=0.82)

    buildings = relationship("BuildingDB", back_populates="campus")


class BuildingDB(Base):
    __tablename__ = "buildings"

    id = Column(String, primary_key=True, index=True)
    campus_id = Column(String, ForeignKey("campuses.id"), nullable=True)
    name = Column(String, nullable=False)
    category = Column(String, default="academic")
    area_sqm = Column(Float, default=5000.0)
    floors = Column(Integer, default=3)
    current_kw = Column(Float, default=150.0)
    load_percent = Column(Integer, default=50)
    status = Column(String, default="normal")

    campus = relationship("CampusDB", back_populates="buildings")
    rooms = relationship("RoomDB", back_populates="building")


class RoomDB(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    room_number = Column(String, nullable=False)
    capacity = Column(Integer, default=30)
    category = Column(String, default="academic")

    building = relationship("BuildingDB", back_populates="rooms")
    devices = relationship("DeviceDB", back_populates="room")


class DeviceDB(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    device_type = Column(String, nullable=False)
    power_rating_w = Column(Float, default=100.0)
    status = Column(String, default="off")

    room = relationship("RoomDB", back_populates="devices")


class ForecastDB(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hour = Column(Integer, nullable=False)
    actual_kwh = Column(Float, nullable=False)
    forecast_kwh = Column(Float, nullable=False)
    model_name = Column(String, default="RandomForest")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    building_id = Column(String, nullable=False)
    building = Column(String, nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, default="medium")
    message = Column(Text)
    recommended_action = Column(Text)
    estimated_waste_kwh = Column(Float, default=0.0)
    estimated_cost_inr = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending / approved / resolved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RecommendationDB(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority_score = Column(Integer, default=50)
    buildings_json = Column(Text, default="[]")
    energy_saved_kwh = Column(Float, default=0.0)
    money_saved_inr = Column(Float, default=0.0)
    co2_reduced_kg = Column(Float, default=0.0)
    applied = Column(Boolean, default=False)
    applied_at = Column(String, nullable=True)


class SimulationDB(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String, nullable=False)
    temp_delta = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    saved_kwh = Column(Float, nullable=False)
    estimated_savings_inr = Column(Float, nullable=False)
    co2_reduced_kg = Column(Float, default=0.0)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SustainabilityReportDB(Base):
    __tablename__ = "sustainability_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_period = Column(String, nullable=False)
    energy_kwh = Column(Float, default=0.0)
    energy_saved_kwh = Column(Float, default=0.0)
    money_saved_inr = Column(Float, default=0.0)
    co2_reduced_kg = Column(Float, default=0.0)
    sustainability_score = Column(Float, default=70.0)


class AgentRunDB(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, index=True, nullable=False)
    stage = Column(Integer, nullable=False)
    stage_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / running / success / failed
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    failure_reason = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, default="jordan-davis")
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ArtifactIngestDB(Base):
    __tablename__ = "artifact_ingests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, index=True, nullable=False)
    artifact_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    schema_valid = Column(Boolean, default=False)
    status = Column(String, default="ingested")  # ingested / rejected / failed
    record_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CostPredictionDB(Base):
    __tablename__ = "cost_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_month = Column(String, nullable=False)
    previous_cost_inr = Column(Float, nullable=False)
    predicted_cost_inr = Column(Float, nullable=False)
    predicted_kwh = Column(Float, nullable=False)
    mom_change_percent = Column(Float, nullable=False)
    optimistic_cost_inr = Column(Float, nullable=False)
    pessimistic_cost_inr = Column(Float, nullable=False)
    drivers_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


