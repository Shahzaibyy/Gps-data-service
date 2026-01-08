"""
MongoDB connection manager for MongoDB Atlas.
Handles connection lifecycle and provides database instance.
"""
from typing import Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ConfigurationError

logger = get_logger(__name__)


class MongoDBManager:
    """
    MongoDB connection manager.
    Handles MongoDB Atlas connection with retry logic.
    """
    
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> AsyncIOMotorDatabase:
        """
        Connect to MongoDB Atlas and return database instance.
        
        Returns:
            AsyncIOMotorDatabase instance
            
        Raises:
            ConfigurationError: If connection fails
        """
        if self._client is not None and self._db is not None:
            logger.warning("MongoDB already connected")
            return self._db
        
        try:
            logger.info(f"Connecting to MongoDB Atlas: {settings.MONGODB_DB_NAME}")
            
            # Create MongoDB client with connection pooling
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=10000,  # 10 seconds timeout
                connectTimeoutMS=20000,  # 20 seconds connect timeout
                retryWrites=True,  # Enable retry writes for transient errors
                retryReads=True,  # Enable retry reads
                appName="GPS-Data-Collection-Service"
            )
            
            # Get database instance
            self._db = self._client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await self._client.admin.command('ping')
            
            # Create basic collections for first-time setup
            try:
                vehicles_collection = await self._db.create_collection("vehicles")
                await vehicles_collection.create_index("vin", unique=True)
                logger.info("Basic collections created successfully")
            except Exception as e:
                logger.warning(f"Failed to create basic collections: {e}")
            
            logger.info(
                f"Successfully connected to MongoDB Atlas",
                extra={
                    "database": settings.MONGODB_DB_NAME,
                    "min_pool_size": settings.MONGODB_MIN_POOL_SIZE,
                    "max_pool_size": settings.MONGODB_MAX_POOL_SIZE
                }
            )
            
            return self._db
            
        except ServerSelectionTimeoutError as e:
            error_msg = (
                f"Failed to connect to MongoDB Atlas. "
                f"Please check your connection string and network access. "
                f"Error: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            
            # Allow startup failure in development mode
            logger.info(f"ALLOW_MONGODB_FAILURE setting: {settings.ALLOW_MONGODB_FAILURE}")
            if settings.ALLOW_MONGODB_FAILURE:
                logger.warning(
                    "MongoDB connection failed but ALLOW_MONGODB_FAILURE=true. "
                    "Application will continue without database connectivity."
                )
                self._db = None
                return None
            else:
                logger.error("ALLOW_MONGODB_FAILURE is false, raising ConfigurationError")
                raise ConfigurationError(
                    error_msg,
                    details={
                        "database": settings.MONGODB_DB_NAME,
                        "error_type": "ServerSelectionTimeout"
                    }
                ) from e
            
        except ConnectionFailure as e:
            error_msg = f"MongoDB connection failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Allow startup failure in development mode
            logger.info(f"ALLOW_MONGODB_FAILURE setting: {settings.ALLOW_MONGODB_FAILURE}")
            if settings.ALLOW_MONGODB_FAILURE:
                logger.warning(
                    "MongoDB connection failed but ALLOW_MONGODB_FAILURE=true. "
                    "Application will continue without database connectivity."
                )
                self._db = None
                return None
            else:
                logger.error("ALLOW_MONGODB_FAILURE is false, raising ConfigurationError")
                raise ConfigurationError(
                    error_msg,
                    details={
                        "database": settings.MONGODB_DB_NAME,
                        "error_type": "ConnectionFailure"
                    }
                ) from e
            
        except Exception as e:
            error_msg = f"Unexpected error connecting to MongoDB: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                details={
                    "database": settings.MONGODB_DB_NAME,
                    "error_type": type(e).__name__
                }
            ) from e
    
    async def disconnect(self):
        """Close MongoDB connection gracefully."""
        if self._client:
            logger.info("Closing MongoDB connection")
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")
    
    async def ping(self) -> bool:
        """
        Ping MongoDB to check connection health.
        
        Returns:
            bool: True if connection is healthy
        """
        try:
            if not self._client:
                return False
            
            await self._client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.error("MongoDB ping failed", exc_info=True)
            return False
    
    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """
        Get database instance.
        
        Returns:
            AsyncIOMotorDatabase instance or None if not connected
        """
        return self._db
    
    def get_client(self) -> AsyncIOMotorClient:
        """
        Get MongoDB client instance.
        
        Returns:
            AsyncIOMotorClient instance
            
        Raises:
            RuntimeError: If not connected
        """
        if self._client is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        
        return self._client


# Global MongoDB manager instance
_mongodb_manager: Optional[MongoDBManager] = None


def get_mongodb_manager() -> MongoDBManager:
    """
    Get global MongoDB manager instance (Singleton).
    
    Returns:
        MongoDBManager instance
    """
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager