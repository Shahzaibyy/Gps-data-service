"""
Odometer data collection job.
Fetches odometer readings for all vehicles.
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


class OdometerJob:
    """
    Scheduled job to collect odometer data.
    """
    
    JOB_NAME = "odometer_collection"
    REPORT_TYPE = ReportType.ODOMETROS
    
    def __init__(
        self,
        gps_provider: IGPSProvider,
        normalization_service: DataNormalizationService,
        repository: Optional[TelemetryRepository],
        vehicle_vins: List[str]
    ):
        self.gps_provider = gps_provider
        self.normalization_service = normalization_service
        self.repository = repository
        self.vehicle_vins = vehicle_vins
    
    async def execute(self) -> JobExecutionLog:
        """Execute the odometer collection job."""
        job_log = JobExecutionLog(
            job_name=self.JOB_NAME,
            job_type="odometer_collection",
            start_time=datetime.utcnow()
        )
        
        try:
            logger.info(f"Starting {self.JOB_NAME} for {len(self.vehicle_vins)} vehicles")
            
            await self.gps_provider.authenticate()
            
            success_count = 0
            failure_count = 0
            errors = []
            
            # Process vehicles in batches
            batch_size = settings.BATCH_SIZE
            max_concurrent = settings.MAX_CONCURRENT_REQUESTS
            
            for i in range(0, len(self.vehicle_vins), batch_size):
                batch_vins = self.vehicle_vins[i:i + batch_size]
                semaphore = asyncio.Semaphore(max_concurrent)
                
                tasks = [
                    self._process_vehicle(vin, semaphore)
                    for vin in batch_vins
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for vin, result in zip(batch_vins, results):
                    if isinstance(result, Exception):
                        failure_count += 1
                        errors.append({"vin": vin, "error": str(result)})
                    elif result:
                        success_count += 1
                    else:
                        failure_count += 1
            
            # Update job log
            job_log.end_time = datetime.utcnow()
            job_log.vehicles_processed = len(self.vehicle_vins)
            job_log.vehicles_succeeded = success_count
            job_log.vehicles_failed = failure_count
            
            if failure_count == 0:
                job_log.status = IngestionStatus.SUCCESS
            elif success_count > 0:
                job_log.status = IngestionStatus.PARTIAL_SUCCESS
            else:
                job_log.status = IngestionStatus.FAILED
            
            if errors:
                job_log.error_summary = {
                    "total_errors": len(errors),
                    "errors": errors[:10]
                }
            
            if self.repository:
                await self.repository.insert_job_log(job_log)
            
            logger.info(
                f"Job {self.JOB_NAME} completed - Success: {success_count}, Failed: {failure_count}"
            )
            
            return job_log
            
        except Exception as e:
            logger.error(f"Job {self.JOB_NAME} failed critically", exc_info=True)
            job_log.end_time = datetime.utcnow()
            job_log.status = IngestionStatus.FAILED
            job_log.error_summary = {"critical_error": str(e)}
            
            if self.repository:
                await self.repository.insert_job_log(job_log)
            
            raise JobExecutionError(f"Job {self.JOB_NAME} execution failed") from e
    
    async def _process_vehicle(self, vin: str, semaphore: asyncio.Semaphore) -> bool:
        """Process odometer data for a single vehicle."""
        async with semaphore:
            try:
                raw_data = await self.gps_provider.get_vehicle_data_by_vin(
                    vin=vin,
                    report_type=self.REPORT_TYPE
                )
                
                if not raw_data or "parsedData" not in raw_data:
                    return False
                
                telemetry_records = self.normalization_service.normalize_report(
                    report_type=self.REPORT_TYPE,
                    raw_data=raw_data
                )
                
                if not telemetry_records:
                    return False
                
                if self.repository:
                    await self.repository.insert_many(telemetry_records)
                
                return True
                
            except Exception as e:
                logger.error(f"Error processing odometer for VIN {vin}", exc_info=True)
                raise


async def run_odometer_job(
    gps_provider: IGPSProvider,
    normalization_service: DataNormalizationService,
    repository: Optional[TelemetryRepository],
    vehicle_vins: List[str]
):
    """Factory function to create and execute the odometer job."""
    job = OdometerJob(
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    return await job.execute()