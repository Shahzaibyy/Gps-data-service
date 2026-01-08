"""
MongoDB repository for vehicle telemetry data.
Implements repository pattern with async operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from app.domain.models.vehicle_telemetry import VehicleTelemetry, JobExecutionLog
from app.domain.models.enums import ReportType, VehicleEventType
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RepositoryError

logger = get_logger(__name__)


class TelemetryRepository:
    """
    Repository for vehicle telemetry data.
    Handles all MongoDB operations for telemetry records.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database connection.
        
        Args:
            db: Motor async MongoDB database instance
        """
        self.db = db
        self.collection: AsyncIOMotorCollection = db[settings.TELEMETRY_COLLECTION]
        self.job_log_collection: AsyncIOMotorCollection = db[settings.JOB_EXECUTION_LOG_COLLECTION]
    
    async def ensure_indexes(self):
        """Create indexes for optimized queries."""
        try:
            # Compound index for common queries
            await self.collection.create_index([
                ("vin", ASCENDING),
                ("recorded_at", DESCENDING)
            ])
            
            await self.collection.create_index([
                ("metadata.report_type", ASCENDING),
                ("recorded_at", DESCENDING)
            ])
            
            await self.collection.create_index([
                ("event_type", ASCENDING),
                ("recorded_at", DESCENDING)
            ])
            
            # TTL index for data retention
            await self.collection.create_index(
                "created_at",
                expireAfterSeconds=settings.TELEMETRY_RETENTION_DAYS * 86400
            )
            
            # Job execution log indexes
            await self.job_log_collection.create_index([
                ("job_name", ASCENDING),
                ("start_time", DESCENDING)
            ])
            
            await self.job_log_collection.create_index(
                "start_time",
                expireAfterSeconds=settings.JOB_LOG_RETENTION_DAYS * 86400
            )
            
            logger.info("Database indexes created successfully")
            
        except PyMongoError as e:
            logger.error("Failed to create indexes", exc_info=True)
            raise RepositoryError("Index creation failed", details={"error": str(e)}) from e
    
    async def insert_one(self, telemetry: VehicleTelemetry) -> str:
        """
        Insert a single telemetry record.
        
        Args:
            telemetry: VehicleTelemetry object to insert
            
        Returns:
            str: Inserted document ID
            
        Raises:
            RepositoryError: If insert fails
        """
        try:
            document = telemetry.model_dump(mode='json')
            result = await self.collection.insert_one(document)
            
            logger.debug(
                f"Inserted telemetry for VIN {telemetry.vin}",
                extra={"vin": telemetry.vin, "id": str(result.inserted_id)}
            )
            
            return str(result.inserted_id)
            
        except PyMongoError as e:
            logger.error(f"Failed to insert telemetry for VIN {telemetry.vin}", exc_info=True)
            raise RepositoryError(
                "Insert operation failed",
                details={"vin": telemetry.vin, "error": str(e)}
            ) from e
    
    async def insert_many(self, telemetry_records: List[VehicleTelemetry]) -> List[str]:
        """
        Insert multiple telemetry records in bulk.
        
        Args:
            telemetry_records: List of VehicleTelemetry objects
            
        Returns:
            List of inserted document IDs
            
        Raises:
            RepositoryError: If bulk insert fails
        """
        if not telemetry_records:
            return []
        
        try:
            documents = [record.model_dump(mode='json') for record in telemetry_records]
            result = await self.collection.insert_many(documents, ordered=False)
            
            logger.info(
                f"Inserted {len(result.inserted_ids)} telemetry records",
                extra={"count": len(result.inserted_ids)}
            )
            
            return [str(id) for id in result.inserted_ids]
            
        except PyMongoError as e:
            logger.error("Bulk insert failed", exc_info=True)
            raise RepositoryError(
                "Bulk insert operation failed",
                details={"count": len(telemetry_records), "error": str(e)}
            ) from e
    
    async def find_by_vin(
        self,
        vin: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[VehicleTelemetry]:
        """
        Find telemetry records by VIN with optional date range.
        
        Args:
            vin: Vehicle Identification Number
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return
            
        Returns:
            List of VehicleTelemetry objects
        """
        try:
            query = {"vin": vin}
            
            if start_date or end_date:
                query["recorded_at"] = {}
                if start_date:
                    query["recorded_at"]["$gte"] = start_date
                if end_date:
                    query["recorded_at"]["$lte"] = end_date
            
            cursor = self.collection.find(query).sort("recorded_at", DESCENDING).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            return [VehicleTelemetry(**doc) for doc in documents]
            
        except PyMongoError as e:
            logger.error(f"Query failed for VIN {vin}", exc_info=True)
            raise RepositoryError(
                "Query operation failed",
                details={"vin": vin, "error": str(e)}
            ) from e
    
    async def find_by_event_type(
        self,
        event_type: VehicleEventType,
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[VehicleTelemetry]:
        """
        Find telemetry records by event type.
        
        Args:
            event_type: Type of vehicle event
            start_date: Optional start date filter
            limit: Maximum number of records
            
        Returns:
            List of VehicleTelemetry objects
        """
        try:
            query = {"event_type": event_type.value}
            
            if start_date:
                query["recorded_at"] = {"$gte": start_date}
            
            cursor = self.collection.find(query).sort("recorded_at", DESCENDING).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            return [VehicleTelemetry(**doc) for doc in documents]
            
        except PyMongoError as e:
            logger.error(f"Query failed for event type {event_type.value}", exc_info=True)
            raise RepositoryError(
                "Query operation failed",
                details={"event_type": event_type.value, "error": str(e)}
            ) from e
    
    async def get_latest_by_vin_and_report_type(
        self,
        vin: str,
        report_type: ReportType
    ) -> Optional[VehicleTelemetry]:
        """
        Get the most recent telemetry record for a VIN and report type.
        
        Args:
            vin: Vehicle Identification Number
            report_type: Type of GPS report
            
        Returns:
            VehicleTelemetry object or None if not found
        """
        try:
            document = await self.collection.find_one(
                {"vin": vin, "metadata.report_type": report_type.value},
                sort=[("recorded_at", DESCENDING)]
            )
            
            if document:
                return VehicleTelemetry(**document)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Query failed for VIN {vin} and report type {report_type.value}", exc_info=True)
            raise RepositoryError(
                "Query operation failed",
                details={"vin": vin, "report_type": report_type.value, "error": str(e)}
            ) from e
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for telemetry data.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict containing statistics
        """
        try:
            match_stage = {}
            if start_date or end_date:
                match_stage["recorded_at"] = {}
                if start_date:
                    match_stage["recorded_at"]["$gte"] = start_date
                if end_date:
                    match_stage["recorded_at"]["$lte"] = end_date
            
            pipeline = [
                {"$match": match_stage} if match_stage else {"$match": {}},
                {
                    "$group": {
                        "_id": None,
                        "total_records": {"$sum": 1},
                        "unique_vins": {"$addToSet": "$vin"},
                        "report_types": {"$addToSet": "$metadata.report_type"},
                        "event_types": {"$addToSet": "$event_type"}
                    }
                },
                {
                    "$project": {
                        "total_records": 1,
                        "unique_vehicle_count": {"$size": "$unique_vins"},
                        "report_types": 1,
                        "event_types": 1
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)
            
            if results:
                return results[0]
            
            return {
                "total_records": 0,
                "unique_vehicle_count": 0,
                "report_types": [],
                "event_types": []
            }
            
        except PyMongoError as e:
            logger.error("Statistics query failed", exc_info=True)
            raise RepositoryError("Statistics operation failed", details={"error": str(e)}) from e
    
    # Job execution log methods
    
    async def insert_job_log(self, job_log: JobExecutionLog) -> str:
        """Insert job execution log."""
        try:
            document = job_log.model_dump(mode='json')
            result = await self.job_log_collection.insert_one(document)
            
            logger.debug(
                f"Inserted job log for {job_log.job_name}",
                extra={"job_name": job_log.job_name}
            )
            
            return str(result.inserted_id)
            
        except PyMongoError as e:
            logger.error(f"Failed to insert job log for {job_log.job_name}", exc_info=True)
            raise RepositoryError(
                "Job log insert failed",
                details={"job_name": job_log.job_name, "error": str(e)}
            ) from e
    
    async def update_job_log(self, log_id: str, update_data: Dict[str, Any]) -> bool:
        """Update job execution log."""
        try:
            from bson import ObjectId
            
            result = await self.job_log_collection.update_one(
                {"_id": ObjectId(log_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except PyMongoError as e:
            logger.error(f"Failed to update job log {log_id}", exc_info=True)
            raise RepositoryError(
                "Job log update failed",
                details={"log_id": log_id, "error": str(e)}
            ) from e
    
    async def get_recent_job_logs(self, job_name: str, limit: int = 10) -> List[JobExecutionLog]:
        """Get recent job execution logs."""
        try:
            cursor = self.job_log_collection.find(
                {"job_name": job_name}
            ).sort("start_time", DESCENDING).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            return [JobExecutionLog(**doc) for doc in documents]
            
        except PyMongoError as e:
            logger.error(f"Failed to fetch job logs for {job_name}", exc_info=True)
            raise RepositoryError(
                "Job log query failed",
                details={"job_name": job_name, "error": str(e)}
            ) from e