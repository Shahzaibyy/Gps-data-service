"""
Voltage health monitoring job.
Monitors GPS device battery voltage for hardware health.
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from app.domain.models.enums import ReportType, IngestionStatus
from app.domain.models.vehicle_telemetry import JobExecutionLog
from app.domain.interfaces.gps_provider import IGPSProvider
from app.application.services.normalization_service import DataNormalizationService
from app.infrastructure.database.repositories.telemetry_repository import TelemetryRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_voltage_health_job(
    gps_provider: IGPSProvider,
    normalization_service: DataNormalizationService,
    repository: Optional[TelemetryRepository],
    vehicle_vins: List[str]
):
    """Voltage health monitoring job."""
    job_log = JobExecutionLog(
        job_name="voltage_health_check",
        job_type="voltage_health",
        start_time=datetime.utcnow()
    )
    
    try:
        logger.info(f"Starting voltage health check for {len(vehicle_vins)} vehicles")
        
        await gps_provider.authenticate()
        
        success_count = 0
        failure_count = 0
        low_voltage_alerts = 0
        
        for vin in vehicle_vins:
            try:
                raw_data = await gps_provider.get_vehicle_data_by_vin(
                    vin=vin,
                    report_type=ReportType.VOLTAGE
                )
                
                if raw_data and "parsedData" in raw_data:
                    telemetry_records = normalization_service.normalize_report(
                        report_type=ReportType.VOLTAGE,
                        raw_data=raw_data
                    )
                    
                    if telemetry_records:
                        # Check for low voltage alerts
                        for record in telemetry_records:
                            if record.voltage and not record.voltage.is_healthy:
                                low_voltage_alerts += 1
                                logger.warning(f"Low voltage alert: VIN {vin}, Voltage: {record.voltage.value}V")
                        
                        if repository:
                            await repository.insert_many(telemetry_records)
                        
                        success_count += 1
                    else:
                        failure_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"Voltage health error for VIN {vin}: {e}")
                failure_count += 1
        
        # Update job log
        job_log.end_time = datetime.utcnow()
        job_log.vehicles_processed = len(vehicle_vins)
        job_log.vehicles_succeeded = success_count
        job_log.vehicles_failed = failure_count
        job_log.status = IngestionStatus.SUCCESS if failure_count == 0 else IngestionStatus.PARTIAL_SUCCESS
        job_log.execution_metadata = {"low_voltage_alerts": low_voltage_alerts}
        
        if repository:
            await repository.insert_job_log(job_log)
        
        logger.info(f"Voltage health check completed - Success: {success_count}, Low voltage alerts: {low_voltage_alerts}")
        
        return job_log
        
    except Exception as e:
        logger.error("Voltage health job failed", exc_info=True)
        job_log.end_time = datetime.utcnow()
        job_log.status = IngestionStatus.FAILED
        
        if repository:
            await repository.insert_job_log(job_log)
        
        return job_log