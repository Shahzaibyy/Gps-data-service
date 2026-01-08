"""
Vehicle domain model.
Represents a vehicle entity in the system.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Vehicle(BaseModel):
    """
    Vehicle entity model.
    Stores basic vehicle information for GPS tracking.
    """
    vin: str = Field(..., description="Vehicle Identification Number (17 characters)", min_length=17, max_length=17)
    vehicle_name: Optional[str] = Field(None, description="GPS provider's internal vehicle identifier (e.g., '1008')")
    make: Optional[str] = Field(None, description="Vehicle manufacturer")
    model: Optional[str] = Field(None, description="Vehicle model")
    year: Optional[int] = Field(None, description="Manufacturing year")
    license_plate: Optional[str] = Field(None, description="License plate number")
    fleet_id: Optional[str] = Field(None, description="Fleet identifier")
    is_active: bool = Field(default=True, description="Whether vehicle is actively tracked")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "vin": "3KPA24BC4NE453663",
                "vehicle_name": "1008",
                "make": "Kia",
                "model": "Rio",
                "year": 2022,
                "license_plate": "ABC-123",
                "fleet_id": "FLEET-001",
                "is_active": True
            }
        }
