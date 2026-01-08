"""
Schema for lastPos (last position) GPS reports.
"""
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.api.schemas.gps_reports.base import VehicleDataBase


class LastPosData(VehicleDataBase):
    """Last position data for a single vehicle."""
    y: Decimal = Field(..., description="Latitude coordinate")
    x: Decimal = Field(..., description="Longitude coordinate")
    t: str = Field(..., description="Timestamp in ISO format (YYYY-MM-DDTHH:MM:SS.mmm)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "3KPA24BC4NE453663",
                "y": 19.340975,
                "x": -99.121057,
                "t": "2024-08-30T12:40:50.000"
            }
        }


class OdometerData(VehicleDataBase):
    """Odometer reading for a single vehicle."""
    odo: str = Field(..., description="Odometer reading with unit (e.g., '111214 km')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "LSGHD52H9ND045496",
                "odo": "111214 km"
            }
        }


class EngineStatusData(VehicleDataBase):
    """Engine status for a single vehicle."""
    engineStatus: str = Field(..., description="Engine status: '0' = off, '1' = on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "3KPA24BC4NE453663",
                "engineStatus": "0"
            }
        }


class IgnitionData(VehicleDataBase):
    """Ignition status for a single vehicle."""
    date: str = Field(..., description="Timestamp of last ignition event")
    ignition: str = Field(..., description="Ignition status: '0' = off, '1' = on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "3KPA24BC4NE453663",
                "date": "2024-08-30T12:39:50.000",
                "ignition": "1"
            }
        }


class SpeedData(VehicleDataBase):
    """Speed data for a single vehicle."""
    date: str = Field(..., description="Timestamp of speed reading")
    speed: str = Field(..., description="Speed with unit (e.g., '46 km/h')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "MEX5B2604NT018260",
                "date": "2024-08-30T12:48:03.000",
                "speed": "46 km/h"
            }
        }


class RecorridosData(VehicleDataBase):
    """Trip summary data (recorridos) for a single vehicle."""
    count: str = Field(..., description="Number of trips")
    totalDuration: str = Field(..., description="Total trip duration (HH:MM:SS)")
    totalKm: str = Field(..., description="Total kilometers with unit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "MEX5B2602NT012229",
                "count": "12",
                "totalDuration": "8:04:33",
                "totalKm": "155 km"
            }
        }


class ParkingEventData(BaseModel):
    """Single parking event."""
    duration: str = Field(..., description="Duration in hours")
    t: str = Field(..., description="Timestamp or 'noData'")
    y: str = Field(..., description="Latitude or 'checkDayBefore'")
    x: str = Field(..., description="Longitude or 'checkDayBefore'")


class EstacionamientosData(VehicleDataBase):
    """Parking events (estacionamientos) for a single vehicle."""
    events: list[ParkingEventData] = Field(default_factory=list, description="List of parking events")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "LSGHD52H9ND045496",
                "events": [
                    {
                        "duration": "4",
                        "t": "noData",
                        "y": "checkDayBefore",
                        "x": "checkDayBefore"
                    }
                ]
            }
        }


class ConsumosData(VehicleDataBase):
    """Fuel consumption data for a single vehicle."""
    km: str = Field(default="", description="Distance traveled")
    timeOnMovement: str = Field(default="", description="Time vehicle was moving")
    calculatedConsumption: str = Field(default="", description="Calculated fuel consumption")
    data: str = Field(default="noData", description="Data availability status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "LSGHD52H9ND045496",
                "km": "",
                "timeOnMovement": "",
                "calculatedConsumption": "",
                "data": "noData"
            }
        }


class VoltageData(VehicleDataBase):
    """Voltage reading for GPS hardware health."""
    voltage: Optional[str] = Field(None, description="Voltage reading with unit")
    timestamp: Optional[str] = Field(None, description="Timestamp of reading")
    
    class Config:
        json_schema_extra = {
            "example": {
                "VIN": "3KPA24BC4NE453663",
                "voltage": "12.4 V",
                "timestamp": "2024-08-30T12:40:50.000"
            }
        }