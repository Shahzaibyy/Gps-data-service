"""
MongoDB repository for vehicle data.
Handles CRUD operations for vehicle entities.
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from app.domain.models.vehicle import Vehicle
from app.core.logging import get_logger
from app.core.exceptions import RepositoryError, VehicleNotFoundError

logger = get_logger(__name__)


class VehicleRepository:
    """
    Repository for vehicle master data.
    Manages vehicle entities in MongoDB.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database connection.
        
        Args:
            db: Motor async MongoDB database instance
        """
        self.db = db
        self.collection: AsyncIOMotorCollection = db["vehicles"]
    
    async def ensure_indexes(self):
        """Create indexes for vehicle collection."""
        try:
            # Unique index on VIN
            await self.collection.create_index("vin", unique=True)
            
            # Index on vehicle_name for GPS provider lookups
            await self.collection.create_index("vehicle_name")
            
            # Index on is_active for filtering active vehicles
            await self.collection.create_index("is_active")
            
            logger.info("Vehicle collection indexes created successfully")
            
        except PyMongoError as e:
            logger.error("Failed to create vehicle indexes", exc_info=True)
            raise RepositoryError("Vehicle index creation failed", details={"error": str(e)}) from e
    
    async def insert_one(self, vehicle: Vehicle) -> str:
        """
        Insert a single vehicle.
        
        Args:
            vehicle: Vehicle object to insert
            
        Returns:
            str: Inserted document ID
            
        Raises:
            RepositoryError: If insert fails or VIN already exists
        """
        try:
            document = vehicle.model_dump(mode='json')
            result = await self.collection.insert_one(document)
            
            logger.info(
                f"Inserted vehicle with VIN {vehicle.vin}",
                extra={"vin": vehicle.vin, "id": str(result.inserted_id)}
            )
            
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.warning(f"Vehicle with VIN {vehicle.vin} already exists")
            raise RepositoryError(
                f"Vehicle with VIN {vehicle.vin} already exists",
                details={"vin": vehicle.vin}
            )
        except PyMongoError as e:
            logger.error(f"Failed to insert vehicle {vehicle.vin}", exc_info=True)
            raise RepositoryError(
                "Vehicle insert operation failed",
                details={"vin": vehicle.vin, "error": str(e)}
            ) from e
    
    async def insert_many(self, vehicles: List[Vehicle]) -> List[str]:
        """
        Insert multiple vehicles in bulk.
        
        Args:
            vehicles: List of Vehicle objects
            
        Returns:
            List of inserted document IDs
            
        Raises:
            RepositoryError: If bulk insert fails
        """
        if not vehicles:
            return []
        
        try:
            documents = [vehicle.model_dump(mode='json') for vehicle in vehicles]
            result = await self.collection.insert_many(documents, ordered=False)
            
            logger.info(
                f"Inserted {len(result.inserted_ids)} vehicles",
                extra={"count": len(result.inserted_ids)}
            )
            
            return [str(id) for id in result.inserted_ids]
            
        except PyMongoError as e:
            logger.error("Bulk vehicle insert failed", exc_info=True)
            raise RepositoryError(
                "Bulk vehicle insert operation failed",
                details={"count": len(vehicles), "error": str(e)}
            ) from e
    
    async def find_by_vin(self, vin: str) -> Optional[Vehicle]:
        """
        Find vehicle by VIN.
        
        Args:
            vin: Vehicle Identification Number
            
        Returns:
            Vehicle object or None if not found
        """
        try:
            document = await self.collection.find_one({"vin": vin})
            
            if document:
                return Vehicle(**document)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Query failed for VIN {vin}", exc_info=True)
            raise RepositoryError(
                "Vehicle query failed",
                details={"vin": vin, "error": str(e)}
            ) from e
    
    async def find_all_active(self) -> List[Vehicle]:
        """
        Find all active vehicles.
        
        Returns:
            List of active Vehicle objects
        """
        try:
            cursor = self.collection.find({"is_active": True})
            documents = await cursor.to_list(length=None)
            
            vehicles = [Vehicle(**doc) for doc in documents]
            
            logger.info(f"Found {len(vehicles)} active vehicles")
            
            return vehicles
            
        except PyMongoError as e:
            logger.error("Failed to fetch active vehicles", exc_info=True)
            raise RepositoryError(
                "Active vehicles query failed",
                details={"error": str(e)}
            ) from e
    
    async def get_all_vins(self, active_only: bool = True) -> List[str]:
        """
        Get list of all VINs.
        
        Args:
            active_only: If True, return only active vehicles
            
        Returns:
            List of VIN strings
        """
        try:
            query = {"is_active": True} if active_only else {}
            cursor = self.collection.find(query, {"vin": 1, "_id": 0})
            documents = await cursor.to_list(length=None)
            
            vins = [doc["vin"] for doc in documents]
            
            logger.info(f"Retrieved {len(vins)} VINs (active_only={active_only})")
            
            return vins
            
        except PyMongoError as e:
            logger.error("Failed to fetch VINs", exc_info=True)
            raise RepositoryError(
                "VIN list query failed",
                details={"error": str(e)}
            ) from e
    
    async def update_vehicle(self, vin: str, update_data: dict) -> bool:
        """
        Update vehicle information.
        
        Args:
            vin: Vehicle Identification Number
            update_data: Dictionary of fields to update
            
        Returns:
            bool: True if updated, False if not found
        """
        try:
            result = await self.collection.update_one(
                {"vin": vin},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated vehicle {vin}")
                return True
            
            return False
            
        except PyMongoError as e:
            logger.error(f"Failed to update vehicle {vin}", exc_info=True)
            raise RepositoryError(
                "Vehicle update failed",
                details={"vin": vin, "error": str(e)}
            ) from e
    
    async def delete_vehicle(self, vin: str) -> bool:
        """
        Delete vehicle by VIN.
        
        Args:
            vin: Vehicle Identification Number
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({"vin": vin})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted vehicle {vin}")
                return True
            
            return False
            
        except PyMongoError as e:
            logger.error(f"Failed to delete vehicle {vin}", exc_info=True)
            raise RepositoryError(
                "Vehicle delete failed",
                details={"vin": vin, "error": str(e)}
            ) from e
    
    async def count_vehicles(self, active_only: bool = True) -> int:
        """
        Count total vehicles.
        
        Args:
            active_only: If True, count only active vehicles
            
        Returns:
            int: Number of vehicles
        """
        try:
            query = {"is_active": True} if active_only else {}
            count = await self.collection.count_documents(query)
            
            return count
            
        except PyMongoError as e:
            logger.error("Failed to count vehicles", exc_info=True)
            raise RepositoryError(
                "Vehicle count failed",
                details={"error": str(e)}
            ) from e
