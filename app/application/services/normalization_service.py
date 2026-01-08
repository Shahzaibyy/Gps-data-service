"""
Data normalization service.
Transforms GPS provider-specific data into canonical domain models.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from app.domain.models.vehicle_telemetry import (
    VehicleTelemetry,
    GeoLocation,
    OdometerReading,
    SpeedReading,
    TripSummary,
    ParkingEvent,
    VoltageReading,
    ConsumptionData,
    IngestionMetadata
)
from app.domain.models.enums import (
    ReportType,
    EngineStatus,
    IgnitionStatus,
    VehicleEventType,
    DataQuality,
    IngestionStatus
)
from app.core.logging import get_logger
from app.core.exceptions import DataNormalizationError

logger = get_logger(__name__)


class DataNormalizationService:
    """
    Service responsible for normalizing GPS provider data.
    Implements the Strategy pattern for different report types.
    """
    
    def __init__(self, provider_name: str = "default"):
        self.provider_name = provider_name
    
    def normalize_report(
        self,
        report_type: ReportType,
        raw_data: Dict[str, Any],
        vehicle_name: Optional[str] = None
    ) -> List[VehicleTelemetry]:
        """
        Normalize raw GPS data into canonical VehicleTelemetry objects.
        
        Args:
            report_type: Type of GPS report
            raw_data: Raw data from GPS provider
            vehicle_name: Optional filter for specific vehicle
            
        Returns:
            List of normalized VehicleTelemetry objects
        """
        try:
            parsed_data = raw_data.get("parsedData", {})
            
            if not parsed_data:
                logger.warning(f"No parsed data found for report type {report_type.value}")
                return []
            
            # Filter by vehicle name if specified
            if vehicle_name and vehicle_name in parsed_data:
                parsed_data = {vehicle_name: parsed_data[vehicle_name]}
            
            # Route to appropriate normalization method
            normalization_methods = {
                ReportType.LAST_POS: self._normalize_last_pos,
                ReportType.ODOMETROS: self._normalize_odometer,
                ReportType.ENGINE_STATUS: self._normalize_engine_status,
                ReportType.IGNITION: self._normalize_ignition,
                ReportType.SPEED: self._normalize_speed,
                ReportType.RECORRIDOS: self._normalize_recorridos,
                ReportType.ESTACIONAMIENTOS: self._normalize_estacionamientos,
                ReportType.CONSUMOS: self._normalize_consumos,
                ReportType.VOLTAGE: self._normalize_voltage,
            }
            
            normalize_func = normalization_methods.get(report_type)
            
            if not normalize_func:
                raise DataNormalizationError(
                    f"No normalization method for report type: {report_type.value}"
                )
            
            telemetry_records = []
            
            for veh_name, vehicle_data in parsed_data.items():
                try:
                    record = normalize_func(veh_name, vehicle_data, report_type)
                    if record:
                        telemetry_records.append(record)
                except Exception as e:
                    logger.error(
                        f"Failed to normalize data for vehicle {veh_name}",
                        exc_info=True,
                        extra={"vehicle_name": veh_name, "vehicle_data": vehicle_data}
                    )
                    # Continue processing other vehicles
                    continue
            
            logger.info(
                f"Normalized {len(telemetry_records)} records for {report_type.value}",
                extra={"report_type": report_type.value, "count": len(telemetry_records)}
            )
            
            return telemetry_records
            
        except Exception as e:
            logger.error(f"Data normalization failed for {report_type.value}", exc_info=True)
            raise DataNormalizationError(
                f"Failed to normalize {report_type.value} data",
                details={"error": str(e), "report_type": report_type.value}
            ) from e
    
    def _normalize_last_pos(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize lastPos data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        # Parse timestamp
        timestamp_str = data.get("t")
        recorded_at = self._parse_timestamp(timestamp_str)
        
        if not recorded_at:
            return None
        
        location = GeoLocation(
            latitude=Decimal(str(data.get("y", 0))),
            longitude=Decimal(str(data.get("x", 0))),
            timestamp=recorded_at
        )
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            location=location,
            event_type=VehicleEventType.POSITION_UPDATE,
            recorded_at=recorded_at,
            metadata=metadata
        )
    
    def _normalize_odometer(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize odometer data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        odo_str = data.get("odo", "")
        
        # Parse "111214 km" format
        odo_value = self._parse_unit_value(odo_str)
        
        if odo_value is None:
            return None
        
        odometer = OdometerReading(
            value=odo_value,
            unit="km",
            timestamp=datetime.utcnow()
        )
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            odometer=odometer,
            event_type=VehicleEventType.ODOMETER_UPDATE,
            recorded_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _normalize_engine_status(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize engine status data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        engine_status_str = data.get("engineStatus", "0")
        engine_status = EngineStatus(int(engine_status_str))
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            engine_status=engine_status,
            event_type=VehicleEventType.ENGINE_STATUS_CHANGE,
            recorded_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _normalize_ignition(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize ignition data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        timestamp_str = data.get("date")
        recorded_at = self._parse_timestamp(timestamp_str)
        
        if not recorded_at or timestamp_str == "noDataInRange":
            recorded_at = datetime.utcnow()
        
        ignition_str = data.get("ignition", "0")
        ignition_status = IgnitionStatus(int(ignition_str))
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            ignition_status=ignition_status,
            event_type=VehicleEventType.IGNITION_CHANGE,
            recorded_at=recorded_at,
            metadata=metadata
        )
    
    def _normalize_speed(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize speed data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        timestamp_str = data.get("date")
        recorded_at = self._parse_timestamp(timestamp_str)
        
        if not recorded_at:
            return None
        
        speed_str = data.get("speed", "0 km/h")
        speed_value = self._parse_unit_value(speed_str)
        
        if speed_value is None:
            speed_value = Decimal(0)
        
        speed = SpeedReading(
            value=speed_value,
            unit="km/h",
            timestamp=recorded_at
        )
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            speed=speed,
            event_type=VehicleEventType.POSITION_UPDATE,
            recorded_at=recorded_at,
            metadata=metadata
        )
    
    def _normalize_recorridos(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize trip summary data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        count = int(data.get("count", 0))
        duration_str = data.get("totalDuration", "0:00:00")
        distance_str = data.get("totalKm", "0 km")
        
        duration_seconds = self._parse_duration(duration_str)
        distance_km = self._parse_unit_value(distance_str)
        
        trips = TripSummary(
            count=count,
            total_duration_seconds=duration_seconds,
            total_distance_km=distance_km
        )
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            trips=trips,
            event_type=VehicleEventType.TRIP_COMPLETED,
            recorded_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _normalize_estacionamientos(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize parking events data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        events_data = data.get("events", [])
        parking_events = []
        
        for event in events_data:
            duration_hours = Decimal(str(event.get("duration", 0)))
            parking_event = ParkingEvent(duration_hours=duration_hours)
            parking_events.append(parking_event)
        
        metadata = self._create_metadata(report_type, data, DataQuality.MEDIUM)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            parking_events=parking_events,
            event_type=VehicleEventType.PARKING_EVENT,
            recorded_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _normalize_consumos(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize consumption data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        data_status = data.get("data", "noData")
        
        if data_status == "noData":
            quality = DataQuality.NO_DATA
        else:
            quality = DataQuality.HIGH
        
        km_str = data.get("km", "")
        distance_km = self._parse_unit_value(km_str) if km_str else None
        
        consumption = ConsumptionData(
            distance_km=distance_km
        )
        
        metadata = self._create_metadata(report_type, data, quality)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            consumption=consumption,
            event_type=VehicleEventType.POSITION_UPDATE,
            recorded_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _normalize_voltage(
        self,
        vehicle_name: str,
        data: Dict[str, Any],
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """Normalize voltage data."""
        vin = data.get("VIN")
        if not vin:
            return None
        
        voltage_str = data.get("voltage", "")
        timestamp_str = data.get("timestamp")
        
        if not voltage_str:
            return None
        
        voltage_value = self._parse_unit_value(voltage_str)
        
        if voltage_value is None:
            return None
        
        recorded_at = self._parse_timestamp(timestamp_str) or datetime.utcnow()
        
        # Typical car battery: 12.4-12.8V is healthy
        is_healthy = Decimal("12.0") <= voltage_value <= Decimal("13.0")
        
        voltage = VoltageReading(
            value=voltage_value,
            unit="V",
            timestamp=recorded_at,
            is_healthy=is_healthy
        )
        
        metadata = self._create_metadata(report_type, data, DataQuality.HIGH)
        
        return VehicleTelemetry(
            vin=vin,
            vehicle_name=vehicle_name,
            voltage=voltage,
            event_type=VehicleEventType.VOLTAGE_ALERT if not is_healthy else VehicleEventType.POSITION_UPDATE,
            recorded_at=recorded_at,
            metadata=metadata
        )
    
    # Utility methods
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime."""
        if not timestamp_str or timestamp_str in ("noData", "noDataInRange"):
            return None
        
        try:
            # Handle format: "2024-08-30T12:30:45.000"
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception as e:
            logger.warning(f"Failed to parse timestamp: {timestamp_str}", exc_info=True)
            return None
    
    def _parse_unit_value(self, value_str: str) -> Optional[Decimal]:
        """Parse value with unit (e.g., '111214 km' -> Decimal(111214))."""
        if not value_str:
            return None
        
        try:
            # Remove unit and parse number
            numeric_part = value_str.split()[0].replace(",", "")
            return Decimal(numeric_part)
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse unit value: {value_str}", exc_info=True)
            return None
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string (HH:MM:SS) to seconds."""
        if not duration_str or duration_str == "0:00:00":
            return 0
        
        try:
            parts = duration_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse duration: {duration_str}", exc_info=True)
            return None
    
    def _create_metadata(
        self,
        report_type: ReportType,
        raw_data: Dict[str, Any],
        quality: DataQuality
    ) -> IngestionMetadata:
        """Create ingestion metadata."""
        return IngestionMetadata(
            provider_name=self.provider_name,
            report_type=report_type,
            data_quality=quality,
            raw_data=raw_data,
            ingestion_status=IngestionStatus.SUCCESS
        )