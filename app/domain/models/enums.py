"""
Domain enumerations for GPS telemetry system.
"""
from enum import Enum


class ReportType(str, Enum):
    """GPS report types supported by the system."""
    CONSUMOS = "consumos"
    ENGINE_STATUS = "engineStatus"
    ESTACIONAMIENTOS = "estacionamientos"
    IGNITION = "ignition"
    LAST_POS = "lastPos"
    ODOMETROS = "odometros"
    RECORRIDOS = "recorridos"
    SIN_MOV = "sinMov"
    SPEED = "speed"
    VOLTAGE = "voltage"


class SearchType(str, Enum):
    """Search operation types."""
    BY_DAY = "searchByDay"
    BY_NAME = "searchByName"
    BY_TIME_RANGE = "searchByTimeRange"
    BY_VIN = "searchByVIN"


class IngestionStatus(str, Enum):
    """Status of data ingestion operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class DataQuality(str, Enum):
    """Data quality indicators."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_DATA = "no_data"


class EngineStatus(int, Enum):
    """Engine on/off status."""
    OFF = 0
    ON = 1


class IgnitionStatus(int, Enum):
    """Ignition status."""
    OFF = 0
    ON = 1


class VehicleEventType(str, Enum):
    """Types of vehicle events tracked."""
    POSITION_UPDATE = "position_update"
    IGNITION_CHANGE = "ignition_change"
    ENGINE_STATUS_CHANGE = "engine_status_change"
    SPEED_VIOLATION = "speed_violation"
    PARKING_EVENT = "parking_event"
    ODOMETER_UPDATE = "odometer_update"
    TRIP_COMPLETED = "trip_completed"
    VOLTAGE_ALERT = "voltage_alert"
    NO_MOVEMENT_DETECTED = "no_movement_detected"


class GPSProviderType(str, Enum):
    """GPS provider implementations."""
    MOCK = "mock"
    REAL = "real"