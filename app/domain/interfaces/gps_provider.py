"""
Abstract interface for GPS providers.
Enables swapping between mock and real implementations without code changes.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.domain.models.enums import ReportType


class IGPSProvider(ABC):
    """
    Abstract GPS Provider interface following Dependency Inversion Principle.
    All GPS provider implementations must adhere to this contract.
    """
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the GPS provider API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_report(
        self,
        report_type: ReportType,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch a specific report from the GPS provider.
        
        Args:
            report_type: Type of report to fetch
            **kwargs: Additional parameters (VIN, date ranges, etc.)
        
        Returns:
            Dict containing the parsed GPS data
            
        Raises:
            GPSProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def get_vehicle_data_by_vin(
        self,
        vin: str,
        report_type: ReportType
    ) -> Dict[str, Any]:
        """
        Fetch data for a specific vehicle by VIN.
        
        Args:
            vin: Vehicle Identification Number
            report_type: Type of data to retrieve
            
        Returns:
            Dict containing vehicle-specific data
        """
        pass
    
    @abstractmethod
    async def get_bulk_report(
        self,
        report_type: ReportType
    ) -> Dict[str, Any]:
        """
        Fetch bulk report for all vehicles.
        
        Args:
            report_type: Type of report to fetch
            
        Returns:
            Dict containing data for all vehicles
            
        Note:
            Bulk reports can be large (250KB+) and slow (7-15 seconds).
            Prefer per-VIN requests when possible.
        """
        pass
    
    @abstractmethod
    async def get_report_by_date(
        self,
        report_type: ReportType,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Fetch report for a specific date.
        
        Args:
            report_type: Type of report
            date: Target date
            
        Returns:
            Dict containing date-specific data
        """
        pass
    
    @abstractmethod
    async def get_report_by_time_range(
        self,
        report_type: ReportType,
        vin: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Fetch report for a vehicle within a time range.
        
        Args:
            report_type: Type of report
            vin: Vehicle Identification Number
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Dict containing time-range data
        """
        pass
    
    @abstractmethod
    async def get_report_by_name(
        self,
        report_type: ReportType,
        vehicle_name: str
    ) -> Dict[str, Any]:
        """
        Fetch report by vehicle name (GPS provider's internal identifier).
        
        Args:
            report_type: Type of report
            vehicle_name: Provider's vehicle identifier (e.g., "1008")
            
        Returns:
            Dict containing vehicle data
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the GPS provider API is accessible and responding.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name/identifier of this GPS provider.
        
        Returns:
            str: Provider name
        """
        pass