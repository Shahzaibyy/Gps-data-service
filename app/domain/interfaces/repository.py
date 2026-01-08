"""
Abstract repository interface.
Defines contract for data persistence operations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.models.vehicle_telemetry import VehicleTelemetry, JobExecutionLog
from app.domain.models.enums import ReportType, VehicleEventType


class IRepository(ABC):
    """
    Abstract repository interface following Repository Pattern.
    All repository implementations must adhere to this contract.
    """
    
    @abstractmethod
    async def ensure_indexes(self):
        """Create necessary database indexes for optimized queries."""
        pass
    
    @abstractmethod
    async def insert_one(self, telemetry: VehicleTelemetry) -> str:
        """
        Insert a single telemetry record.
        
        Args:
            telemetry: VehicleTelemetry object to insert
            
        Returns:
            str: Inserted document ID
        """
        pass
    
    @abstractmethod
    async def insert_many(self, telemetry_records: List[VehicleTelemetry]) -> List[str]:
        """
        Insert multiple telemetry records in bulk.
        
        Args:
            telemetry_records: List of VehicleTelemetry objects
            
        Returns:
            List of inserted document IDs
        """
        pass
    
    @abstractmethod
    async def find_by_vin(
        self,
        vin: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[VehicleTelemetry]:
        """
        Find telemetry records by VIN with optional date range.
        
        Args:
            vin: Vehicle Identification Number
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return
            
        Returns:
            List of VehicleTelemetry objects
        """
        pass
    
    @abstractmethod
    async def find_by_event_type(
        self,
        event_type: VehicleEventType,
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[VehicleTelemetry]:
        """
        Find telemetry records by event type.
        
        Args:
            event_type: Type of vehicle event
            start_date: Optional start date filter
            limit: Maximum number of records
            
        Returns:
            List of VehicleTelemetry objects
        """
        pass
    
    @abstractmethod
    async def get_latest_by_vin_and_report_type(
        self,
        vin: str,
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """
        Get the most recent telemetry record for a VIN and report type.
        
        Args:
            vin: Vehicle Identification Number
            report_type: Type of GPS report
            
        Returns:
            VehicleTelemetry object or None if not found
        """
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for telemetry data.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict containing statistics
        """
        pass
    
    @abstractmethod
    async def insert_job_log(self, job_log: JobExecutionLog) -> str:
        """Insert job execution log."""
        pass
    
    @abstractmethod
    async def update_job_log(self, log_id: str, update_data: Dict[str, Any]) -> bool:
        """Update job execution log."""
        pass
    
    @abstractmethod
    async def get_recent_job_logs(self, job_name: str, limit: int = 10) -> List[JobExecutionLog]:
        """Get recent job execution logs."""
        pass