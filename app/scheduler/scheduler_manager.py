"""
APScheduler management for cron-based GPS data collection jobs.
"""
import asyncio
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SchedulerManager:
    """
    Manages APScheduler for executing scheduled GPS data collection jobs.
    Supports idempotent execution, monitoring, and graceful shutdown.
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._jobs_registry = {}
    
    def initialize(self):
        """Initialize the scheduler with MongoDB job store or memory store."""
        try:
            # Check if MongoDB is available
            from app.infrastructure.database.mongodb import get_mongodb_manager
            mongodb_manager = get_mongodb_manager()
            db = mongodb_manager.get_database()
            
            # Use memory job store for now to avoid APScheduler MongoDB issues
            jobstores = {}
            logger.warning("Scheduler initialized with memory job store (using memory store for now)")
            
            job_defaults = settings.SCHEDULER_JOB_DEFAULTS
            
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                job_defaults=job_defaults,
                timezone=settings.SCHEDULER_TIMEZONE
            )
            
            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )
            
            logger.info(
                "Scheduler initialized",
                extra={"timezone": settings.SCHEDULER_TIMEZONE}
            )
            
        except Exception as e:
            logger.error("Failed to initialize scheduler", exc_info=True)
            raise
    
    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str,
        description: str = "",
        **kwargs
    ):
        """
        Add a cron-scheduled job.
        
        Args:
            func: Async function to execute
            job_id: Unique identifier for the job
            cron_expression: Cron expression (e.g., "*/5 * * * *")
            description: Human-readable job description
            **kwargs: Additional arguments to pass to the job function
        """
        try:
            # Parse cron expression: "minute hour day month day_of_week"
            parts = cron_expression.split()
            
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4] if len(parts) > 4 else '*'
            )
            
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=description or job_id,
                replace_existing=True,
                kwargs=kwargs
            )
            
            self._jobs_registry[job_id] = {
                "function": func.__name__,
                "cron": cron_expression,
                "description": description
            }
            
            logger.info(
                f"Cron job added: {job_id}",
                extra={
                    "job_id": job_id,
                    "cron": cron_expression,
                    "description": description
                }
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to add cron job: {job_id}", exc_info=True)
            raise
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized. Call initialize() first.")
        
        try:
            self.scheduler.start()
            logger.info("Scheduler started")
            logger.info(
                f"Active jobs: {len(self._jobs_registry)}",
                extra={"jobs": list(self._jobs_registry.keys())}
            )
        except Exception as e:
            logger.error("Failed to start scheduler", exc_info=True)
            raise
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler gracefully.
        
        Args:
            wait: If True, wait for running jobs to complete
        """
        if self.scheduler:
            logger.info("Shutting down scheduler", extra={"wait": wait})
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown complete")
    
    def pause_job(self, job_id: str):
        """Pause a specific job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
        except Exception as e:
            logger.error(f"Failed to pause job: {job_id}", exc_info=True)
            raise
    
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
        except Exception as e:
            logger.error(f"Failed to resume job: {job_id}", exc_info=True)
            raise
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self._jobs_registry:
                del self._jobs_registry[job_id]
            logger.info(f"Job removed: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job: {job_id}", exc_info=True)
            raise
    
    def get_jobs(self):
        """Get list of all scheduled jobs."""
        if not self.scheduler:
            return []
        
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": None,  # Simplified for now
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    
    def _job_executed_listener(self, event):
        """Event listener for job execution."""
        if event.exception:
            logger.error(
                f"Job {event.job_id} failed",
                extra={
                    "job_id": event.job_id,
                    "exception": str(event.exception)
                },
                exc_info=event.exception
            )
        else:
            logger.info(
                f"Job {event.job_id} executed successfully",
                extra={"job_id": event.job_id}
            )


# Global scheduler instance
_scheduler_manager = None


def get_scheduler_manager() -> SchedulerManager:
    """Get global scheduler manager instance."""
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager