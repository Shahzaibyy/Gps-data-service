"""
Mock GPS Provider implementation for development and testing.
Returns realistic static data matching the GPS API schema.
"""
import asyncio
import json
from typing import Dict, Any
from datetime import datetime
from app.domain.interfaces.gps_provider import IGPSProvider
from app.domain.models.enums import ReportType
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockGPSProvider(IGPSProvider):
    """
    Mock implementation of GPS Provider.
    Returns static JSON responses matching real GPS API format.
    Simulates realistic latency for testing.
    """
    
    def __init__(self, simulate_latency: bool = True):
        self.simulate_latency = simulate_latency
        self._authenticated = False
        self._mock_data = self._initialize_mock_data()
    
    def _initialize_mock_data(self) -> Dict[str, Any]:
        """Initialize mock data for all report types."""
        return {
            ReportType.LAST_POS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "y": 19.899827, "x": -99.222737, "t": "2024-08-30T12:30:45.000"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "y": 19.340975, "x": -99.121057, "t": "2024-08-30T12:40:50.000"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "y": 19.365197, "x": -99.265575, "t": "2024-08-01T13:55:27.000"},
                    "1010": {"VIN": "MEX5B2605NT017117", "y": 19.64507, "x": -99.17114, "t": "2024-08-30T12:41:04.000"},
                    "1011": {"VIN": "MEX5B2602NT012229", "y": 19.397855, "x": -99.235578, "t": "2024-08-30T12:40:54.000"}
                }
            },
            ReportType.ODOMETROS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "odo": "111214 km"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "odo": "70870 km"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "odo": "117964 km"},
                    "1010": {"VIN": "MEX5B2605NT017117", "odo": "45115 km"},
                    "1011": {"VIN": "MEX5B2602NT012229", "odo": "96691 km"}
                }
            },
            ReportType.ENGINE_STATUS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "engineStatus": "0"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "engineStatus": "0"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "engineStatus": "0"},
                    "1010": {"VIN": "MEX5B2605NT017117", "engineStatus": "0"},
                    "1011": {"VIN": "MEX5B2602NT012229", "engineStatus": "0"}
                }
            },
            ReportType.IGNITION: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "date": "2024-08-30T12:30:45.000", "ignition": "0"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "date": "2024-08-30T12:39:50.000", "ignition": "1"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "date": "noDataInRange", "ignition": "0"},
                    "1010": {"VIN": "MEX5B2605NT017117", "date": "2024-08-30T12:39:42.000", "ignition": "0"},
                    "1011": {"VIN": "MEX5B2602NT012229", "date": "2024-08-30T12:39:47.000", "ignition": "1"}
                }
            },
            ReportType.SPEED: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "date": "2024-08-30T12:30:45.000", "speed": "0 km/h"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "date": "2024-08-30T12:47:58.000", "speed": "0 km/h"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "date": "2024-08-01T13:55:27.000", "speed": "0 km/h"},
                    "1010": {"VIN": "MEX5B2605NT017117", "date": "2024-08-30T12:46:38.000", "speed": "0 km/h"},
                    "1011": {"VIN": "MEX5B2602NT012229", "date": "2024-08-30T12:46:48.000", "speed": "16 km/h"}
                }
            },
            ReportType.RECORRIDOS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "count": "3", "totalDuration": "3:02:43", "totalKm": "100 km"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "count": "14", "totalDuration": "3:51:42", "totalKm": "59 km"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "count": "0", "totalDuration": "0:00:00", "totalKm": "0.00 km"},
                    "1010": {"VIN": "MEX5B2605NT017117", "count": "11", "totalDuration": "0:00:00", "totalKm": "0.00 km"},
                    "1011": {"VIN": "MEX5B2602NT012229", "count": "12", "totalDuration": "8:04:33", "totalKm": "155 km"}
                }
            },
            ReportType.ESTACIONAMIENTOS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "events": [{"duration": "4", "t": "noData", "y": "checkDayBefore", "x": "checkDayBefore"}]},
                    "1008": {"VIN": "3KPA24BC4NE453663", "events": [{"duration": "14", "t": "noData", "y": "checkDayBefore", "x": "checkDayBefore"}]},
                    "1009": {"VIN": "3KPA24BC2NE460675", "events": [{"duration": "0", "t": "noData", "y": "checkDayBefore", "x": "checkDayBefore"}]},
                    "1010": {"VIN": "MEX5B2605NT017117", "events": [{"duration": "12", "t": "noData", "y": "checkDayBefore", "x": "checkDayBefore"}]}
                }
            },
            ReportType.CONSUMOS: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "km": "", "timeOnMovement": "", "calculatedConsumption": "", "data": "noData"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "km": "", "timeOnMovement": "", "calculatedConsumption": "", "data": "noData"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "km": "", "timeOnMovement": "", "calculatedConsumption": "", "data": "noData"}
                }
            },
            ReportType.VOLTAGE: {
                "parsedData": {
                    "1006": {"VIN": "LSGHD52H9ND045496", "voltage": "12.6 V", "timestamp": "2024-08-30T12:30:45.000"},
                    "1008": {"VIN": "3KPA24BC4NE453663", "voltage": "12.4 V", "timestamp": "2024-08-30T12:40:50.000"},
                    "1009": {"VIN": "3KPA24BC2NE460675", "voltage": "11.8 V", "timestamp": "2024-08-01T13:55:27.000"}
                }
            }
        }
    
    async def _simulate_network_delay(self, min_delay: float = 0.1, max_delay: float = 2.0):
        """Simulate realistic network latency."""
        if self.simulate_latency:
            import random
            await asyncio.sleep(random.uniform(min_delay, max_delay))
    
    async def authenticate(self) -> bool:
        """Simulate authentication."""
        logger.info("Mock GPS Provider: Authenticating")
        await self._simulate_network_delay(0.5, 1.0)
        self._authenticated = True
        return True
    
    async def get_report(
        self,
        report_type: ReportType,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch mock report data."""
        logger.info(f"Mock GPS Provider: Fetching {report_type.value} report", extra={"kwargs": kwargs})
        await self._simulate_network_delay()
        
        if report_type in self._mock_data:
            return self._mock_data[report_type]
        
        return {"parsedData": {}}
    
    async def get_vehicle_data_by_vin(
        self,
        vin: str,
        report_type: ReportType
    ) -> Dict[str, Any]:
        """Fetch mock data for specific VIN."""
        logger.info(f"Mock GPS Provider: Fetching {report_type.value} for VIN {vin}")
        await self._simulate_network_delay(0.5, 1.5)
        
        report_data = self._mock_data.get(report_type, {}).get("parsedData", {})
        
        # Find vehicle by VIN in existing mock data
        for vehicle_name, vehicle_data in report_data.items():
            if vehicle_data.get("VIN") == vin:
                return {"parsedData": {vehicle_name: vehicle_data}}
        
        # If VIN not found in mock data, generate random data
        logger.debug(f"VIN {vin} not in mock data, generating random response")
        random_data = self._generate_random_data_for_vin(vin, report_type)
        
        if random_data:
            # Use a random vehicle name for unknown VINs
            import random
            vehicle_name = f"rand_{random.randint(2000, 9999)}"
            return {"parsedData": {vehicle_name: random_data}}
        
        return {"parsedData": {}}
    
    async def get_bulk_report(
        self,
        report_type: ReportType
    ) -> Dict[str, Any]:
        """Fetch bulk mock report (simulates slower response)."""
        logger.info(f"Mock GPS Provider: Fetching bulk {report_type.value} report")
        await self._simulate_network_delay(5.0, 10.0)  # Bulk is slower
        
        return self._mock_data.get(report_type, {"parsedData": {}})
    
    async def get_report_by_date(
        self,
        report_type: ReportType,
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch mock report for specific date."""
        logger.info(f"Mock GPS Provider: Fetching {report_type.value} for date {date.strftime('%d-%m-%Y')}")
        await self._simulate_network_delay()
        
        return self._mock_data.get(report_type, {"parsedData": {}})
    
    async def get_report_by_time_range(
        self,
        report_type: ReportType,
        vin: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch mock report for time range."""
        logger.info(
            f"Mock GPS Provider: Fetching {report_type.value} for VIN {vin} "
            f"from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
        )
        await self._simulate_network_delay(1.0, 3.0)
        
        # Time range queries typically return single data point (as per docs)
        return await self.get_vehicle_data_by_vin(vin, report_type)
    
    async def get_report_by_name(
        self,
        report_type: ReportType,
        vehicle_name: str
    ) -> Dict[str, Any]:
        """Fetch mock report by vehicle name."""
        logger.info(f"Mock GPS Provider: Fetching {report_type.value} for vehicle name {vehicle_name}")
        await self._simulate_network_delay()
        
        report_data = self._mock_data.get(report_type, {}).get("parsedData", {})
        
        if vehicle_name in report_data:
            return {"parsedData": {vehicle_name: report_data[vehicle_name]}}
        
        return {"parsedData": {}}
    
    async def health_check(self) -> bool:
        """Mock health check."""
        logger.debug("Mock GPS Provider: Health check")
        await self._simulate_network_delay(0.1, 0.3)
        return True
    
    def _generate_random_data_for_vin(self, vin: str, report_type: ReportType) -> Dict[str, Any]:
        """Generate random GPS data for unknown VINs."""
        import random
        from datetime import datetime, timedelta
        
        # Generate random timestamp within last 24 hours
        now = datetime.utcnow()
        random_time = now - timedelta(hours=random.randint(0, 24))
        timestamp = random_time.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        base_data = {"VIN": vin}
        
        if report_type == ReportType.LAST_POS:
            # Random coordinates around Mexico City area
            base_lat, base_lon = 19.4326, -99.1332
            lat_offset = random.uniform(-0.5, 0.5)
            lon_offset = random.uniform(-0.5, 0.5)
            
            return {
                **base_data,
                "y": base_lat + lat_offset,
                "x": base_lon + lon_offset,
                "t": timestamp
            }
        
        elif report_type == ReportType.ODOMETROS:
            return {
                **base_data,
                "odo": f"{random.randint(10000, 200000)} km"
            }
        
        elif report_type == ReportType.ENGINE_STATUS:
            return {
                **base_data,
                "engineStatus": str(random.choice([0, 1]))
            }
        
        elif report_type == ReportType.IGNITION:
            return {
                **base_data,
                "date": timestamp,
                "ignition": str(random.choice([0, 1]))
            }
        
        elif report_type == ReportType.SPEED:
            return {
                **base_data,
                "date": timestamp,
                "speed": f"{random.randint(0, 120)} km/h"
            }
        
        elif report_type == ReportType.RECORRIDOS:
            return {
                **base_data,
                "count": str(random.randint(0, 20)),
                "totalDuration": f"{random.randint(0, 12)}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
                "totalKm": f"{random.randint(0, 500)} km"
            }
        
        elif report_type == ReportType.ESTACIONAMIENTOS:
            return {
                **base_data,
                "events": [{
                    "duration": str(random.randint(1, 24)),
                    "t": "noData",
                    "y": "checkDayBefore",
                    "x": "checkDayBefore"
                }]
            }
        
        elif report_type == ReportType.CONSUMOS:
            return {
                **base_data,
                "km": f"{random.randint(0, 100)} km" if random.choice([True, False]) else "",
                "timeOnMovement": f"{random.randint(0, 8)}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}" if random.choice([True, False]) else "",
                "calculatedConsumption": f"{random.uniform(5.0, 15.0):.1f} L/100km" if random.choice([True, False]) else "",
                "data": random.choice(["noData", "available"])
            }
        
        elif report_type == ReportType.VOLTAGE:
            voltage = random.uniform(11.5, 13.0)
            return {
                **base_data,
                "voltage": f"{voltage:.1f} V",
                "timestamp": timestamp
            }
        
        return base_data

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "mock_gps_provider"