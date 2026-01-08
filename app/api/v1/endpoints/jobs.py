"""
Job management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from app.scheduler.scheduler_manager import get_scheduler_manager
from app.infrastructure.database.mongodb import get_mongodb_manager
from app.infrastructure.database.repositories.telemetry_repository import TelemetryRepository
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class JobInfo(BaseModel):
    """Job information response model."""
    id: str
    name: str
    next_run_time: Optional[str] = None
    trigger: str


class JobExecutionSummary(BaseModel):
    """Job execution summary model."""
    job_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    vehicles_processed: int
    vehicles_succeeded: int
    vehicles_failed: int
    success_rate: float
    duration_seconds: Optional[float]


@router.get("/", response_model=List[JobInfo])
async def list_jobs():
    """
    List all scheduled jobs.
    
    Returns:
        List of active scheduled jobs
    """
    try:
        scheduler = get_scheduler_manager()
        jobs = scheduler.get_jobs()
        
        return [
            JobInfo(
                id=job["id"],
                name=job["name"],
                next_run_time=job["next_run_time"],
                trigger=job["trigger"]
            )
            for job in jobs
        ]
    except Exception as e:
        logger.error("Failed to list jobs", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )


@router.post("/{job_id}/pause")
async def pause_job(job_id: str):
    """
    Pause a scheduled job.
    
    Args:
        job_id: Job identifier
    """
    try:
        scheduler = get_scheduler_manager()
        scheduler.pause_job(job_id)
        
        logger.info(f"Job paused via API: {job_id}")
        
        return {
            "message": f"Job {job_id} paused successfully",
            "job_id": job_id,
            "status": "paused"
        }
    except Exception as e:
        logger.error(f"Failed to pause job {job_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause job: {str(e)}"
        )


@router.post("/{job_id}/resume")
async def resume_job(job_id: str):
    """
    Resume a paused job.
    
    Args:
        job_id: Job identifier
    """
    try:
        scheduler = get_scheduler_manager()
        scheduler.resume_job(job_id)
        
        logger.info(f"Job resumed via API: {job_id}")
        
        return {
            "message": f"Job {job_id} resumed successfully",
            "job_id": job_id,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Failed to resume job {job_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume job: {str(e)}"
        )


@router.get("/{job_name}/history", response_model=List[JobExecutionSummary])
async def get_job_history(job_name: str, limit: int = 10):
    """
    Get execution history for a specific job.
    
    Args:
        job_name: Name of the job
        limit: Maximum number of records to return (default: 10)
    """
    try:
        mongodb_manager = get_mongodb_manager()
        db = mongodb_manager.get_database()
        repository = TelemetryRepository(db)
        
        job_logs = await repository.get_recent_job_logs(job_name, limit)
        
        return [
            JobExecutionSummary(
                job_name=log.job_name,
                start_time=log.start_time,
                end_time=log.end_time,
                status=log.status.value,
                vehicles_processed=log.vehicles_processed,
                vehicles_succeeded=log.vehicles_succeeded,
                vehicles_failed=log.vehicles_failed,
                success_rate=log.success_rate,
                duration_seconds=log.duration_seconds
            )
            for log in job_logs
        ]
    except Exception as e:
        logger.error(f"Failed to get job history for {job_name}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job history: {str(e)}"
        )


@router.get("/statistics")
async def get_job_statistics():
    """
    Get overall job execution statistics.
    """
    try:
        mongodb_manager = get_mongodb_manager()
        db = mongodb_manager.get_database()
        
        # Aggregate job statistics
        pipeline = [
            {
                "$group": {
                    "_id": "$job_name",
                    "total_executions": {"$sum": 1},
                    "successful_executions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    },
                    "failed_executions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    },
                    "avg_duration_seconds": {"$avg": "$duration_seconds"},
                    "avg_success_rate": {"$avg": "$success_rate"}
                }
            }
        ]
        
        cursor = db.job_execution_logs.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return {
            "statistics": [
                {
                    "job_name": result["_id"],
                    "total_executions": result["total_executions"],
                    "successful_executions": result["successful_executions"],
                    "failed_executions": result["failed_executions"],
                    "avg_duration_seconds": round(result.get("avg_duration_seconds", 0), 2),
                    "avg_success_rate": round(result.get("avg_success_rate", 0), 2)
                }
                for result in results
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get job statistics", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job statistics: {str(e)}"
        )