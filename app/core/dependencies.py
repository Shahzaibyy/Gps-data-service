"""
Dependency injection container.
Provides centralized dependency management.
"""
from typing import Optional
from app.domain.interfaces.gps_provider import IGPSProvider
from app.infrastructure.gps_providers.mock_provider import MockGPSProvider
from app.application.services.normalization_service import DataNormalizationService
from app.infrastructure.database.repositories.telemetry_repository import TelemetryRepository
from app.infrastructure.database.repositories.vehicle_repository import VehicleRepository
from app.infrastructure.database.mongodb import get_mongodb_manager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DependencyContainer:
    """
    Dependency container following Dependency Injection pattern.
    Manages service lifecycle and dependencies.
    """
    
    def __init__(self):
        self._gps_provider: Optional[IGPSProvider] = None
        self._normalization_service: Optional[DataNormalizationService] = None
        self._repository: Optional[TelemetryRepository] = None
        self._vehicle_repository: Optional[VehicleRepository] = None
    
    async def initialize(self):
        """Initialize all dependencies."""
        logger.info("Initializing dependency container")
        
        # Initialize GPS provider
        self._gps_provider = await self._create_gps_provider()
        
        # Initialize normalization service
        self._normalization_service = DataNormalizationService(
            provider_name=self._gps_provider.get_provider_name()
        )
        
        # Initialize repository
        mongodb_manager = get_mongodb_manager()
        db = mongodb_manager.get_database()
        
        if db is not None:
            self._repository = TelemetryRepository(db)
            await self._repository.ensure_indexes()
            logger.info("Telemetry repository initialized with MongoDB connection")
            
            self._vehicle_repository = VehicleRepository(db)
            await self._vehicle_repository.ensure_indexes()
            logger.info("Vehicle repository initialized with MongoDB connection")
        else:
            logger.warning("Repositories not initialized - MongoDB not connected")
            self._repository = None
            self._vehicle_repository = None
        
        logger.info("Dependency container initialized successfully")
    
    async def _create_gps_provider(self) -> IGPSProvider:
        """Create GPS provider based on configuration."""
        if settings.GPS_PROVIDER_TYPE == "mock":
            logger.info("Creating Mock GPS Provider")
            provider = MockGPSProvider(simulate_latency=not settings.DEBUG)
        else:
            # TODO: Implement real GPS provider
            logger.error(f"GPS provider type '{settings.GPS_PROVIDER_TYPE}' not implemented")
            raise NotImplementedError(f"GPS provider '{settings.GPS_PROVIDER_TYPE}' not available")
        
        # Authenticate
        try:
            authenticated = await provider.authenticate()
            if not authenticated:
                logger.warning("GPS provider authentication failed")
        except Exception as e:
            logger.error("GPS provider authentication error", exc_info=True)
            raise
        
        return provider
    
    def get_gps_provider(self) -> IGPSProvider:
        """Get GPS provider instance."""
        if self._gps_provider is None:
            raise RuntimeError("GPS provider not initialized. Call initialize() first.")
        return self._gps_provider
    
    def get_normalization_service(self) -> DataNormalizationService:
        """Get normalization service instance."""
        if self._normalization_service is None:
            raise RuntimeError("Normalization service not initialized. Call initialize() first.")
        return self._normalization_service
    
    def get_repository(self) -> Optional[TelemetryRepository]:
        """Get repository instance. Returns None if MongoDB is not connected."""
        return self._repository
    
    def get_vehicle_repository(self) -> Optional[VehicleRepository]:
        """Get vehicle repository instance. Returns None if MongoDB is not connected."""
        return self._vehicle_repository
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up dependency container")
        
        # Add cleanup logic here if needed
        self._gps_provider = None
        self._normalization_service = None
        self._repository = None
        self._vehicle_repository = None
        
        logger.info("Dependency container cleaned up")


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get global dependency container instance."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container