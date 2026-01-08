"""
Configuration management using Pydantic Settings.
Supports environment-based configuration with validation.
"""
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "GPS Data Collection Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # GPS Provider Configuration
    GPS_PROVIDER_TYPE: str = Field(default="mock", pattern="^(mock|real)$")
    GPS_API_BASE_URL: str = "http://base_url:3000"
    GPS_API_ENDPOINT: str = "/prod/prod"
    GPS_API_USERNAME: str = "user_name"
    GPS_API_PASSWORD: str = "password"
    GPS_API_TIMEOUT: int = 30  # seconds
    GPS_API_MAX_RETRIES: int = 3
    GPS_API_RETRY_BACKOFF: float = 2.0  # exponential backoff multiplier
    
    # Concurrency Control
    MAX_CONCURRENT_REQUESTS: int = 10
    BATCH_SIZE: int = 50  # vehicles per batch
    RATE_LIMIT_REQUESTS_PER_SECOND: float = 5.0
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "gps_telemetry"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MAX_IDLE_TIME_MS: int = 45000
    
    # Development Mode
    ALLOW_MONGODB_FAILURE: bool = False
    
    # Collections
    TELEMETRY_COLLECTION: str = "vehicle_telemetry"
    JOB_EXECUTION_LOG_COLLECTION: str = "job_execution_logs"
    
    # Scheduler Configuration
    SCHEDULER_TIMEZONE: str = "America/Mexico_City"
    SCHEDULER_JOB_DEFAULTS: dict = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 300  # 5 minutes
    }
    
    # Job Schedules (Cron expressions)
    JOB_VEHICLE_POSITION_CRON: str = "*/5 * * * *"  # Every 5 minutes
    JOB_ODOMETER_CRON: str = "0 */6 * * *"  # Every 6 hours
    JOB_ENGINE_STATUS_CRON: str = "*/10 * * * *"  # Every 10 minutes
    JOB_SPEED_MONITORING_CRON: str = "*/5 * * * *"  # Every 5 minutes
    JOB_IGNITION_CRON: str = "*/15 * * * *"  # Every 15 minutes
    JOB_VOLTAGE_HEALTH_CRON: str = "0 0 * * *"  # Daily at midnight
    
    # Data Retention
    TELEMETRY_RETENTION_DAYS: int = 90
    JOB_LOG_RETENTION_DAYS: int = 30
    
    # Observability
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_TRACING: bool = False
    JAEGER_AGENT_HOST: Optional[str] = None
    JAEGER_AGENT_PORT: Optional[int] = None
    
    # Alert Thresholds
    ALERT_MAX_JOB_DURATION_SECONDS: int = 600  # 10 minutes
    ALERT_MAX_FAILURE_RATE: float = 0.1  # 10%
    
    @field_validator("MONGODB_URL")
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        """Ensure MongoDB URL is valid."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URL must start with mongodb:// or mongodb+srv://")
        return v
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use this function throughout the application to access settings.
    """
    return Settings()


# Export for convenience
settings = get_settings()