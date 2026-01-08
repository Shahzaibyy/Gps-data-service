"""
Vehicle position data collection job.
Fetches last position for all vehicles using per-VIN requests.
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


class VehiclePositionJob:
    """
    Scheduled job to collect vehicle position data.
    Uses concurrent per-VIN requests for optimal performance.
    """
    
    JOB_NAME = "vehicle_position_collection"
    REPORT_TYPE = ReportType.LAST_POS
    
    def __init__(
        self,
        gps_provider: IGPSProvider,
        normalization_service: DataNormalizationService,
        repository: Optional[TelemetryRepository],
        vehicle_vins: List[str]
    ):
        """
        Initialize job with dependencies.
        
        Args:
            gps_provider: GPS provider implementation
            normalization_service: Data normalization service
            repository: Telemetry repository
            vehicle_vins: List of VINs to process
        """
        self.gps_provider = gps_provider
        self.normalization_service = normalization_service
        self.repository = repository
        self.vehicle_vins = vehicle_vins
    
    async def execute(self) -> JobExecutionLog:
        """
        Execute the job: fetch, normalize, and store position data.
        
        Returns:
            JobExecutionLog with execution metrics
        """
        job_log = JobExecutionLog(
            job_name=self.JOB_NAME,
            job_type="position_collection",
            start_time=datetime.utcnow()
        )
        
        try:
            logger.info(
                f"Starting {self.JOB_NAME}",
                extra={"vehicle_count": len(self.vehicle_vins)}
            )
            
            # Authenticate if needed
            await self.gps_provider.authenticate()
            
            # Process vehicles in concurrent batches
            batch_size = settings.BATCH_SIZE
            max_concurrent = settings.MAX_CONCURRENT_REQUESTS
            
            success_count = 0
            failure_count = 0
            errors = []
            
            for i in range(0, len(self.vehicle_vins), batch_size):
                batch_vins = self.vehicle_vins[i:i + batch_size]
                
                # Create semaphore to limit concurrency
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
                        logger.error(
                            f"Failed to process VIN {vin}",
                            exc_info=result,
                            extra={"vin": vin}
                        )
                    elif result:
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append({"vin": vin, "error": "No data returned"})
                
                logger.info(
                    f"Batch processed: {success_count}/{len(batch_vins)} succeeded",
                    extra={"batch_index": i // batch_size}
                )
            
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
                    "errors": errors[:10]  # Store first 10 errors
                }
            
            # Save job log
            if self.repository is not None:
                await self.repository.insert_job_log(job_log)
            else:
                logger.warning("Job log not saved - repository not available")
            
            logger.info(
                f"Job {self.JOB_NAME} completed",
                extra={
                    "status": job_log.status.value,
                    "success_rate": job_log.success_rate,
                    "duration_seconds": job_log.duration_seconds
                }
            )
            
            return job_log
            
        except Exception as e:
            logger.error(f"Job {self.JOB_NAME} failed critically", exc_info=True)
            
            job_log.end_time = datetime.utcnow()
            job_log.status = IngestionStatus.FAILED
            job_log.error_summary = {"critical_error": str(e)}
            
            try:
                if self.repository is not None:
                    await self.repository.insert_job_log(job_log)
                else:
                    logger.warning("Failed job log not saved - repository not available")
            except Exception as log_error:
                logger.error("Failed to save job log", exc_info=log_error)
            
            raise JobExecutionError(
                f"Job {self.JOB_NAME} execution failed",
                details={"error": str(e)}
            ) from e
    
    async def _process_vehicle(self, vin: str, semaphore: asyncio.Semaphore) -> bool:
        """
        Process a single vehicle's position data.
        
        Args:
            vin: Vehicle Identification Number
            semaphore: Concurrency control semaphore
            
        Returns:
            bool: True if successful, False otherwise
        """
        async with semaphore:
            try:
                # Fetch data from GPS provider
                raw_data = await self.gps_provider.get_vehicle_data_by_vin(
                    vin=vin,
                    report_type=self.REPORT_TYPE
                )
                
                if not raw_data or "parsedData" not in raw_data:
                    logger.warning(f"No data returned for VIN {vin}")
                    return False
                
                # Normalize data
                telemetry_records = self.normalization_service.normalize_report(
                    report_type=self.REPORT_TYPE,
                    raw_data=raw_data
                )
                
                if not telemetry_records:
                    logger.warning(f"No telemetry records after normalization for VIN {vin}")
                    return False
                
                # Store in database
                if self.repository is not None:
                    await self.repository.insert_many(telemetry_records)
                else:
                    logger.warning(f"Telemetry data not saved for VIN {vin} - repository not available")
                
                logger.debug(
                    f"Successfully processed VIN {vin}",
                    extra={"vin": vin, "records_count": len(telemetry_records)}
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Error processing VIN {vin}", exc_info=True)
                raise


async def run_vehicle_position_job(
    gps_provider: IGPSProvider,
    normalization_service: DataNormalizationService,
    repository: Optional[TelemetryRepository],
    vehicle_vins: List[str]
):
    """
    Factory function to create and execute the job.
    Used by the scheduler.
    """
    job = VehiclePositionJob(
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    return await job.execute()