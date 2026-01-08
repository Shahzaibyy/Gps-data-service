"""
Base schemas for GPS API requests and responses.
"""
from typing import Dict, Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from app.domain.models.enums import ReportType


class GPSAuthRequest(BaseModel):
    """Authentication request for GPS API."""
    user: str = Field(..., description="Username for GPS API")
    password: str = Field(..., description="Password for GPS API")


class GPSReportRequest(BaseModel):
    """Base request schema for GPS reports."""
    reportType: ReportType = Field(..., description="Type of report to retrieve")
    startDate: Optional[str] = Field(None, description="Start date in DD-MM-YYYY format")
    endDate: Optional[str] = Field(None, description="End date in DD-MM-YYYY format")
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")
    name: Optional[str] = Field(None, description="Vehicle name/identifier")


T = TypeVar('T')


class GPSAPIResponse(BaseModel, Generic[T]):
    """Standardized GPS API response wrapper."""
    statusCode: int = Field(..., description="HTTP status code")
    headers: Dict[str, Any] = Field(default_factory=dict)
    body: str = Field(..., description="JSON string containing parsed data")
    
    def get_parsed_body(self) -> Dict[str, Any]:
        """Parse the body JSON string into a dictionary."""
        import json
        return json.loads(self.body)


class GPSParsedData(BaseModel):
    """
    Base class for parsed GPS data.
    Each vehicle's data is keyed by vehicle name (e.g., "1006", "1008").
    """
    parsedData: Dict[str, Any] = Field(..., description="Parsed vehicle data keyed by vehicle name")


class VehicleDataBase(BaseModel):
    """Base model for individual vehicle data in GPS responses."""
    VIN: str = Field(..., description="Vehicle Identification Number")
    
    class Config:
        extra = "allow"  # Allow additional fields from GPS provider