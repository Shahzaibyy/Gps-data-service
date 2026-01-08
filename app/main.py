"""
FastAPI application entry point.
Bootstraps the GPS data collection microservice with MongoDB Atlas.
"""
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.dependencies import get_container
from app.api.v1.router import api_router
from app.infrastructure.database.mongodb import get_mongodb_manager
from app.scheduler.scheduler_manager import get_scheduler_manager
from app.application.jobs.vehicle_position_job import run_vehicle_position_job
from app.application.jobs.odometer_job import run_odometer_job
from app.application.jobs.engine_status_job import run_engine_status_job
from app.application.jobs.speed_monitoring_job import run_speed_monitoring_job
from app.application.jobs.ignition_job import run_ignition_job
from app.application.jobs.voltage_health_job import run_voltage_health_job

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown tasks.
    """
    # ============ STARTUP ============
    logger.info("=" * 60)
    logger.info("Starting GPS Data Collection Service")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info("=" * 60)
    
    try:
        # 1. Connect to MongoDB Atlas
        logger.info("Connecting to MongoDB Atlas...")
        mongodb_manager = get_mongodb_manager()
        db = await mongodb_manager.connect()
        if db is not None:
            logger.info("✓ MongoDB Atlas connection established")
        else:
            logger.warning("⚠ MongoDB Atlas connection failed - running in degraded mode")
        
        # 2. Initialize dependency container
        logger.info("Initializing dependency container...")
        container = get_container()
        await container.initialize()
        logger.info("✓ Dependency container initialized")
        
        # 3. Initialize and start scheduler
        logger.info("Initializing scheduler...")
        scheduler = get_scheduler_manager()
        scheduler.initialize()
        
        # Register scheduled jobs
        await _register_scheduled_jobs(scheduler, container)
        
        scheduler.start()
        logger.info("✓ Scheduler started with registered jobs")
        
        logger.info("=" * 60)
        logger.info("GPS Data Collection Service started successfully!")
        logger.info(f"API Documentation: http://localhost:8000/docs")
        logger.info("=" * 60)
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", exc_info=True)
        raise
    
    # ============ SHUTDOWN ============
    logger.info("=" * 60)
    logger.info("Shutting down GPS Data Collection Service")
    logger.info("=" * 60)
    
    try:
        # 1. Stop scheduler
        logger.info("Stopping scheduler...")
        scheduler = get_scheduler_manager()
        scheduler.shutdown(wait=True)
        logger.info("✓ Scheduler stopped")
        
        # 2. Cleanup dependencies
        logger.info("Cleaning up dependencies...")
        container = get_container()
        await container.cleanup()
        logger.info("✓ Dependencies cleaned up")
        
        # 3. Close MongoDB connection
        logger.info("Closing MongoDB connection...")
        mongodb_manager = get_mongodb_manager()
        await mongodb_manager.disconnect()
        logger.info("✓ MongoDB connection closed")
        
        logger.info("=" * 60)
        logger.info("Shutdown complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Error during shutdown", exc_info=True)


async def _register_scheduled_jobs(scheduler, container):
    """Register all scheduled jobs with the scheduler."""
    
    # Get dependencies from container
    gps_provider = container.get_gps_provider()
    normalization_service = container.get_normalization_service()
    repository = container.get_repository()
    vehicle_repository = container.get_vehicle_repository()
    
    # Fetch vehicle VINs from database
    if vehicle_repository is not None:
        try:
            vehicle_vins = await vehicle_repository.get_all_vins(active_only=True)
            logger.info(f"Loaded {len(vehicle_vins)} active vehicles from database")
        except Exception as e:
            logger.error("Failed to load vehicles from database", exc_info=True)
            logger.warning("Falling back to empty vehicle list")
            vehicle_vins = []
    else:
        logger.warning("Vehicle repository not available - no vehicles will be processed")
        vehicle_vins = []
    
    if not vehicle_vins:
        logger.warning(
            "No vehicles found in database. "
            "Please run 'python scripts/seed_mock_vehicles.py' to populate vehicles."
        )
        return
    
    logger.info(f"Registering jobs for {len(vehicle_vins)} vehicles")
    
    # Job 1: Vehicle Position Collection
    scheduler.add_cron_job(
        func=run_vehicle_position_job,
        job_id="vehicle_position_collection",
        cron_expression=settings.JOB_VEHICLE_POSITION_CRON,
        description="Collect vehicle position data for all vehicles",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    # Job 2: Odometer Collection
    scheduler.add_cron_job(
        func=run_odometer_job,
        job_id="odometer_collection",
        cron_expression=settings.JOB_ODOMETER_CRON,
        description="Collect odometer readings for all vehicles",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    # Job 3: Engine Status Monitoring
    scheduler.add_cron_job(
        func=run_engine_status_job,
        job_id="engine_status_monitoring",
        cron_expression=settings.JOB_ENGINE_STATUS_CRON,
        description="Monitor engine status for all vehicles",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    # Job 4: Speed Monitoring
    scheduler.add_cron_job(
        func=run_speed_monitoring_job,
        job_id="speed_monitoring",
        cron_expression=settings.JOB_SPEED_MONITORING_CRON,
        description="Monitor vehicle speeds and detect violations",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    # Job 5: Ignition Monitoring
    scheduler.add_cron_job(
        func=run_ignition_job,
        job_id="ignition_monitoring",
        cron_expression=settings.JOB_IGNITION_CRON,
        description="Monitor ignition status for all vehicles",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    # Job 6: Voltage Health Check
    scheduler.add_cron_job(
        func=run_voltage_health_job,
        job_id="voltage_health_check",
        cron_expression=settings.JOB_VOLTAGE_HEALTH_CRON,
        description="Monitor GPS device voltage health",
        gps_provider=gps_provider,
        normalization_service=normalization_service,
        repository=repository,
        vehicle_vins=vehicle_vins
    )
    
    jobs = scheduler.get_jobs()
    logger.info(f"✓ Registered {len(jobs)} scheduled jobs")
    
    for job in jobs:
        logger.info(
            f"  - {job['name']} (Next run: {job['next_run_time']})",
            extra={"job_id": job["id"], "trigger": job["trigger"]}
        )


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise GPS IoT Data Collection Microservice for Vehicle Telemetry",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - Service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "mongodb_database": settings.MONGODB_DB_NAME,
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Root level health check endpoint.
    Used by Docker healthcheck and load balancers.
    """
    from app.infrastructure.database.mongodb import get_mongodb_manager
    
    # Check MongoDB connection
    mongodb_manager = get_mongodb_manager()
    db = mongodb_manager.get_database()
    mongodb_healthy = False
    
    if db is not None:
        try:
            mongodb_healthy = await mongodb_manager.ping()
        except Exception:
            mongodb_healthy = False
    
    # Check scheduler
    from app.scheduler.scheduler_manager import get_scheduler_manager
    scheduler = get_scheduler_manager()
    scheduler_healthy = False
    
    try:
        scheduler_healthy = scheduler.scheduler is not None and scheduler.scheduler.running
    except Exception:
        scheduler_healthy = False
    
    # Overall health
    healthy = mongodb_healthy and scheduler_healthy
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "mongodb": "healthy" if mongodb_healthy else "unhealthy",
            "scheduler": "healthy" if scheduler_healthy else "unhealthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )