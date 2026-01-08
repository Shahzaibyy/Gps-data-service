"""
Engine status monitoring job.
Monitors engine on/off status for all vehicles.
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from app.domain.models.enums import ReportType, IngestionStatus
from app.domain.models.vehicle_telemetry import JobExecutionLog
from app.domain.interfaces.gps_provider import IGPSProvider
from app.application.services.normalization_service import DataNormalizationService
from app.infrastructure.database.repositories.telemetry_repository import TelemetryRepository
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import JobExecutionError

logger = get_logger(__name__)


async def run_engine_status_job(
    gps_provider: IGPSProvider,
    normalization_service: DataNormalizationService,
    repository: Optional[TelemetryRepository],
    vehicle_vins: List[str]
):
    """Engine status monitoring job."""
    job_log = JobExecutionLog(
        job_name="engine_status_monitoring",
        job_type="engine_status",
        start_time=datetime.utcnow()
    )
    
    try:
        logger.info(f"Starting engine status monitoring for {len(vehicle_vins)} vehicles")
        
        await gps_provider.authenticate()
        
        success_count = 0
        failure_count = 0
        
        # Process in smaller batches for engine status
        batch_size = min(settings.BATCH_SIZE, 25)
        
        for i in range(0, len(vehicle_vins), batch_size):
            batch_vins = vehicle_vins[i:i + batch_size]
            
            for vin in batch_vins:
                try:
                    raw_data = await gps_provider.get_vehicle_data_by_vin(
                        vin=vin,
                        report_type=ReportType.ENGINE_STATUS
                    )
                    
                    if raw_data and "parsedData" in raw_data:
                        telemetry_records = normalization_service.normalize_report(
                            report_type=ReportType.ENGINE_STATUS,
                            raw_data=raw_data
                        )
                        
                        if telemetry_records and repository:
                            await repository.insert_many(telemetry_records)
                            success_count += 1
                        else:
                            failure_count += 1
                    else:
                        failure_count += 1
                        
                except Exception as e:
                    logger.error(f"Engine status error for VIN {vin}: {e}")
                    failure_count += 1
        
        # Update job log
        job_log.end_time = datetime.utcnow()
        job_log.vehicles_processed = len(vehicle_vins)
        job_log.vehicles_succeeded = success_count
        job_log.vehicles_failed = failure_count
        job_log.status = IngestionStatus.SUCCESS if failure_count == 0 else IngestionStatus.PARTIAL_SUCCESS
        
        if repository:
            await repository.insert_job_log(job_log)
        
        logger.info(f"Engine status job completed - Success: {success_count}, Failed: {failure_count}")
        
        return job_log
        
    except Exception as e:
        logger.error("Engine status job failed", exc_info=True)
        job_log.end_time = datetime.utcnow()
        job_log.status = IngestionStatus.FAILED
        job_log.error_summary = {"error": str(e)}
        
        if repository:
            await repository.insert_job_log(job_log)
        
        raise JobExecutionError("Engine status job failed") from e