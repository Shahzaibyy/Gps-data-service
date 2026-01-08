# GPS Data Collection Service - Setup Guide

## 🎯 Overview

This guide walks you through setting up the GPS IoT data ingestion microservice with **mock data** following best practices (SOLID, DRY, Clean Architecture).

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account (already configured)
- Poetry or pip

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# The .env file is already configured with MongoDB Atlas credentials
# No changes needed for development
```

### Step 3: Seed Mock Vehicle Data

**Important:** The database needs vehicle records before the scheduler can run.

```bash
# Run the seeding script
python scripts/seed_mock_vehicles.py
```

**What this does:**
- Connects to MongoDB Atlas
- Creates `vehicles` collection with indexes
- Inserts 5 mock vehicles with VINs matching the GPS provider
- Verifies the data

**Expected Output:**
```
============================================================
Starting Mock Vehicle Data Seeding
============================================================
Connecting to MongoDB...
✓ MongoDB connected
✓ Vehicle repository initialized
Existing vehicles in database: 0
Inserting 5 mock vehicles...
  ✓ Inserted: LSGHD52H9ND045496 (1006)
  ✓ Inserted: 3KPA24BC4NE453663 (1008)
  ✓ Inserted: 3KPA24BC2NE460675 (1009)
  ✓ Inserted: MEX5B2605NT017117 (1010)
  ✓ Inserted: MEX5B2602NT012229 (1011)
============================================================
Seeding Complete!
  Inserted: 5
  Skipped:  0
  Total:    5
============================================================
```

### Step 4: Start the Application

```bash
# Using Poetry
poetry run python -m app.main

# Or directly
python -m app.main

# Or using uvicorn
uvicorn app.main:app --reload
```

**Expected Startup Log:**
```
============================================================
Starting GPS Data Collection Service
Environment: development
Debug Mode: True
============================================================
Connecting to MongoDB Atlas...
✓ MongoDB Atlas connection established
Initializing dependency container...
✓ Dependency container initialized
Initializing scheduler...
Loaded 5 active vehicles from database
Registering jobs for 5 vehicles
✓ Registered 1 scheduled jobs
  - vehicle_position_collection (Next run: ...)
✓ Scheduler started with registered jobs
============================================================
GPS Data Collection Service started successfully!
API Documentation: http://localhost:8000/docs
============================================================
```

### Step 5: Verify the System

**Check API Health:**
```bash
curl http://localhost:8000/health
```

**View API Documentation:**
```
http://localhost:8000/docs
```

**List Scheduled Jobs:**
```bash
curl http://localhost:8000/api/v1/jobs/
```

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION STARTUP                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Connect to MongoDB Atlas                                 │
│  2. Initialize Repositories (Vehicle + Telemetry)            │
│  3. Fetch Active VINs from 'vehicles' Collection             │
│  4. Register Scheduled Jobs with VINs                        │
│  5. Start APScheduler                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULED JOB EXECUTION                   │
│                    (Every 5 minutes)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        │                                       │
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│  For Each VIN    │                  │  Concurrent      │
│  from Database   │                  │  Processing      │
└──────────────────┘                  └──────────────────┘
        ↓                                       ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Call Mock GPS Provider API                               │
│     - Provider returns static JSON matching real schema      │
│     - Simulates network latency                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Normalize GPS Data                                       │
│     - Parse raw GPS response                                 │
│     - Convert to canonical VehicleTelemetry model            │
│     - Add metadata (provider, quality, timestamps)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Store in MongoDB                                         │
│     - Insert into 'vehicle_telemetry' collection             │
│     - Log job execution metrics                              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Database Collections

### 1. `vehicles` Collection

**Purpose:** Master data for vehicles being tracked

**Schema:**
```json
{
  "vin": "3KPA24BC4NE453663",
  "vehicle_name": "1008",
  "make": "Kia",
  "model": "Rio",
  "year": 2022,
  "license_plate": "MEX-1008",
  "fleet_id": "FLEET-001",
  "is_active": true,
  "created_at": "2024-01-07T10:00:00Z",
  "updated_at": "2024-01-07T10:00:00Z"
}
```

**Indexes:**
- `vin` (unique)
- `vehicle_name`
- `is_active`

### 2. `vehicle_telemetry` Collection

**Purpose:** Normalized GPS telemetry data

**Schema:**
```json
{
  "vin": "3KPA24BC4NE453663",
  "vehicle_name": "1008",
  "location": {
    "latitude": 19.340975,
    "longitude": -99.121057,
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  "speed": {
    "value": 0,
    "unit": "km/h",
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  "engine_status": 0,
  "ignition_status": 1,
  "event_type": "position_update",
  "metadata": {
    "provider_name": "mock_gps_provider",
    "report_type": "lastPos",
    "ingestion_timestamp": "2024-01-07T10:05:00Z",
    "ingestion_status": "success",
    "data_quality": "high",
    "raw_data": { ... }
  },
  "recorded_at": "2024-08-30T12:40:50.000Z",
  "created_at": "2024-01-07T10:05:00Z",
  "updated_at": "2024-01-07T10:05:00Z"
}
```

**Indexes:**
- `(vin, recorded_at)`
- `(metadata.report_type, recorded_at)`
- `(event_type, recorded_at)`
- TTL index on `created_at` (90 days retention)

### 3. `job_execution_logs` Collection

**Purpose:** Track job execution metrics

**Schema:**
```json
{
  "job_name": "vehicle_position_collection",
  "job_type": "position_collection",
  "start_time": "2024-01-07T10:05:00Z",
  "end_time": "2024-01-07T10:05:45Z",
  "status": "success",
  "vehicles_processed": 5,
  "vehicles_succeeded": 5,
  "vehicles_failed": 0,
  "error_summary": null
}
```

## 🧪 Testing the System

### 1. Verify Vehicles are Loaded

```bash
# Check MongoDB directly
mongosh "mongodb+srv://..." --eval "db.vehicles.find().pretty()"

# Or use the API (if you add an endpoint)
```

### 2. Monitor Job Execution

```bash
# Watch logs
tail -f logs/app.log

# Check job history via API
curl http://localhost:8000/api/v1/jobs/vehicle_position_collection/history?limit=5
```

### 3. Query Telemetry Data

```bash
# Check MongoDB
mongosh "mongodb+srv://..." --eval "db.vehicle_telemetry.find().limit(5).pretty()"
```

### 4. Job Statistics

```bash
curl http://localhost:8000/api/v1/jobs/statistics
```

## 🔧 Configuration

### Cron Schedule (Default: Every 5 minutes)

Edit `.env`:
```bash
JOB_VEHICLE_POSITION_CRON="*/5 * * * *"  # Every 5 minutes
```

### Concurrency Settings

```bash
MAX_CONCURRENT_REQUESTS=10    # Parallel API calls
BATCH_SIZE=50                 # Vehicles per batch
RATE_LIMIT_REQUESTS_PER_SECOND=5.0
```

### Data Retention

```bash
TELEMETRY_RETENTION_DAYS=90   # Auto-delete after 90 days
JOB_LOG_RETENTION_DAYS=30     # Keep logs for 30 days
```

## 🐛 Troubleshooting

### No Vehicles Found

**Error:**
```
No vehicles found in database. Please run 'python scripts/seed_mock_vehicles.py'
```

**Solution:**
```bash
python scripts/seed_mock_vehicles.py
```

### MongoDB Connection Failed

**Error:**
```
Failed to connect to MongoDB Atlas
```

**Solutions:**
1. Check MongoDB Atlas network access (whitelist your IP)
2. Verify connection string in `.env`
3. Test connection:
   ```bash
   mongosh "mongodb+srv://..."
   ```

### Jobs Not Running

**Check:**
1. Scheduler status: `curl http://localhost:8000/api/v1/jobs/`
2. Application logs for errors
3. Verify vehicles exist: Run seeding script

## 📝 Adding More Vehicles

### Option 1: Modify Seeding Script

Edit `scripts/seed_mock_vehicles.py` and add more vehicles to `MOCK_VEHICLES` list.

### Option 2: Manual Insert

```python
from app.domain.models.vehicle import Vehicle
from app.infrastructure.database.mongodb import get_mongodb_manager
from app.infrastructure.database.repositories.vehicle_repository import VehicleRepository

# Create vehicle
vehicle = Vehicle(
    vin="YOUR17DIGITVIN123",
    vehicle_name="1012",
    make="Toyota",
    model="Camry",
    year=2023,
    is_active=True
)

# Insert (async context required)
# ... repository.insert_one(vehicle)
```

## 🎯 Next Steps

1. ✅ Seed mock vehicles
2. ✅ Start application
3. ✅ Verify jobs are running
4. ✅ Check telemetry data is being stored
5. 🔄 Monitor job execution logs
6. 🔄 Add more report types (odometer, speed, etc.)
7. 🔄 Implement real GPS provider when ready

## 📚 Architecture Principles

This implementation follows:

- **SOLID Principles**
  - Single Responsibility: Each class has one job
  - Open/Closed: Easy to extend with new providers
  - Liskov Substitution: Mock/Real providers are interchangeable
  - Interface Segregation: Clean interfaces (IGPSProvider)
  - Dependency Inversion: Depend on abstractions, not concretions

- **DRY (Don't Repeat Yourself)**
  - Reusable repositories
  - Shared normalization logic
  - Common error handling

- **Clean Architecture**
  - Domain layer (models, interfaces)
  - Application layer (services, jobs)
  - Infrastructure layer (repositories, providers)
  - API layer (endpoints)

## 🔐 Security Notes

- MongoDB credentials are in `.env` (never commit this file)
- Use environment variables in production
- Implement authentication for API endpoints in production
- Enable MongoDB Atlas IP whitelist

## 📞 Support

For issues or questions, check:
- Application logs
- MongoDB Atlas dashboard
- API documentation at `/docs`
