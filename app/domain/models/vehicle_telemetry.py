"""
Canonical domain models for normalized vehicle telemetry.
These models represent the standardized format for all GPS data.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.domain.models.enums import (
    ReportType, 
    DataQuality, 
    IngestionStatus,
    EngineStatus,
    IgnitionStatus,
    VehicleEventType
)


class GeoLocation(BaseModel):
    """Geographic coordinates."""
    latitude: Decimal = Field(..., description="Latitude in decimal degrees")
    longitude: Decimal = Field(..., description="Longitude in decimal degrees")
    timestamp: datetime = Field(..., description="When this position was recorded")
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: Decimal) -> Decimal:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: Decimal) -> Decimal:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class OdometerReading(BaseModel):
    """Odometer measurement."""
    value: Decimal = Field(..., description="Odometer reading in kilometers")
    unit: str = Field(default="km", description="Unit of measurement")
    timestamp: datetime = Field(..., description="When this reading was taken")


class SpeedReading(BaseModel):
    """Speed measurement."""
    value: Decimal = Field(..., description="Speed value")
    unit: str = Field(default="km/h", description="Speed unit")
    timestamp: datetime = Field(..., description="When this speed was recorded")


class TripSummary(BaseModel):
    """Summary of vehicle trips."""
    count: int = Field(..., description="Number of trips")
    total_duration_seconds: Optional[int] = Field(None, description="Total trip duration")
    total_distance_km: Optional[Decimal] = Field(None, description="Total distance traveled")


class ParkingEvent(BaseModel):
    """Parking event details."""
    duration_hours: Decimal = Field(..., description="Duration of parking")
    location: Optional[GeoLocation] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class VoltageReading(BaseModel):
    """GPS device voltage reading for hardware health monitoring."""
    value: Decimal = Field(..., description="Voltage value")
    unit: str = Field(default="V", description="Voltage unit")
    timestamp: datetime = Field(..., description="When this reading was taken")
    is_healthy: bool = Field(default=True, description="Whether voltage is within acceptable range")


class ConsumptionData(BaseModel):
    """Fuel/energy consumption data."""
    distance_km: Optional[Decimal] = None
    time_on_movement_seconds: Optional[int] = None
    calculated_consumption: Optional[Decimal] = None
    unit: str = Field(default="L/100km", description="Consumption unit")


class IngestionMetadata(BaseModel):
    """Metadata about the data ingestion process."""
    provider_name: str = Field(..., description="GPS provider identifier")
    report_type: ReportType = Field(..., description="Type of GPS report")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ingestion_status: IngestionStatus = Field(default=IngestionStatus.SUCCESS)
    data_quality: DataQuality = Field(default=DataQuality.HIGH)
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original raw data from provider")
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)


class VehicleTelemetry(BaseModel):
    """
    Canonical normalized vehicle telemetry model.
    This is the single source of truth for all vehicle data in the system.
    """
    # Vehicle Identification
    vin: str = Field(..., description="Vehicle Identification Number", min_length=17, max_length=17)
    vehicle_name: Optional[str] = Field(None, description="GPS provider's vehicle identifier")
    
    # Location & Movement
    location: Optional[GeoLocation] = None
    speed: Optional[SpeedReading] = None
    odometer: Optional[OdometerReading] = None
    
    # Vehicle Status
    engine_status: Optional[EngineStatus] = None
    ignition_status: Optional[IgnitionStatus] = None
    
    # Operational Data
    trips: Optional[TripSummary] = None
    parking_events: Optional[List[ParkingEvent]] = None
    consumption: Optional[ConsumptionData] = None
    
    # Hardware Health
    voltage: Optional[VoltageReading] = None
    is_stationary: Optional[bool] = Field(None, description="Whether vehicle has not moved for extended period")
    days_without_movement: Optional[int] = None
    
    # Event Classification
    event_type: VehicleEventType = Field(..., description="Type of event this record represents")
    
    # Metadata
    metadata: IngestionMetadata = Field(..., description="Ingestion and data quality metadata")
    
    # Timestamps
    recorded_at: datetime = Field(..., description="When the GPS device recorded this data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this record was created in our system")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "vin": "3KPA24BC4NE453663",
                "vehicle_name": "1008",
                "location": {
                    "latitude": 19.340975,
                    "longitude": -99.121057,
                    "timestamp": "2024-08-30T12:40:50.000Z"
                },
                "speed": {
                    "value": 0,
                    "unit": "km/h",
                    "timestamp": "2024-08-30T12:40:50.000Z"
                },
                "engine_status": 0,
                "ignition_status": 1,
                "event_type": "position_update",
                "recorded_at": "2024-08-30T12:40:50.000Z"
            }
        }


class JobExecutionLog(BaseModel):
    """Log entry for scheduled job executions."""
    job_name: str = Field(..., description="Name of the executed job")
    job_type: str = Field(..., description="Type/category of job")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: IngestionStatus = Field(default=IngestionStatus.PENDING)
    vehicles_processed: int = Field(default=0)
    vehicles_succeeded: int = Field(default=0)
    vehicles_failed: int = Field(default=0)
    error_summary: Optional[Dict[str, Any]] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.vehicles_processed == 0:
            return 0.0
        return (self.vehicles_succeeded / self.vehicles_processed) * 100