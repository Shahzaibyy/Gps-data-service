# GPS Data Collection Service - Complete Architecture Schema

## 🏗️ System Overview

This document provides a comprehensive schema of the GPS IoT data collection microservice, detailing the complete data flow from vehicle data ingestion to storage, including all API interactions, database schemas, and system components.

## 📊 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GPS DATA COLLECTION SERVICE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   FastAPI App   │    │   APScheduler   │    │  MongoDB Atlas  │             │
│  │                 │    │                 │    │                 │             │
│  │ • Health Checks │    │ • Cron Jobs     │    │ • Vehicle Data  │             │
│  │ • Job Management│    │ • Job Registry  │    │ • Telemetry     │             │
│  │ • API Endpoints │    │ • Event Logs    │    │ • Job Logs      │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                       │                       │                     │
│           └───────────────────────┼───────────────────────┘                     │
│                                   │                                             │
│  ┌─────────────────────────────────┼─────────────────────────────────┐           │
│  │                    SCHEDULED JOBS (6 Types)                      │           │
│  │                                 │                                 │           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │           │
│  │  │ Position    │ │ Odometer    │ │ Engine      │ │ Speed       │  │           │
│  │  │ Every 2min  │ │ Every 3min  │ │ Every 4min  │ │ Every 2min  │  │           │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │           │
│  │                                                                   │           │
│  │  ┌─────────────┐ ┌─────────────┐                                  │           │
│  │  │ Ignition    │ │ Voltage     │                                  │           │
│  │  │ Every 5min  │ │ Every 6min  │                                  │           │
│  │  └─────────────┘ └─────────────┘                                  │           │
│  └───────────────────────────────────────────────────────────────────┘           │
│                                   │                                             │
│  ┌─────────────────────────────────┼─────────────────────────────────┐           │
│  │                    DATA PROCESSING LAYER                         │           │
│  │                                 │                                 │           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │           │
│  │  │ Vehicle     │ │ GPS Provider│ │Normalization│ │ Repository  │  │           │
│  │  │ Repository  │ │ (Mock)      │ │ Service     │ │ Layer       │  │           │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │           │
│  └───────────────────────────────────────────────────────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Complete Data Flow Schema

### Phase 1: Application Startup

```mermaid
sequenceDiagram
    participant App as FastAPI App
    participant DB as MongoDB Atlas
    participant VR as Vehicle Repository
    participant Sched as APScheduler
    participant Jobs as Job Registry

    App->>DB: Connect to MongoDB Atlas
    DB-->>App: Connection Established
    
    App->>VR: Initialize Vehicle Repository
    VR->>DB: Create Indexes (vin, vehicle_name, is_active)
    DB-->>VR: Indexes Created
    
    App->>VR: Fetch Active Vehicle VINs
    VR->>DB: Query: db.vehicles.find({is_active: true})
    DB-->>VR: Return VIN List
    VR-->>App: List of Active VINs
    
    App->>Sched: Initialize APScheduler
    App->>Jobs: Register 6 Cron Jobs with VINs
    Jobs-->>Sched: Jobs Registered
    
    Sched->>Sched: Start Scheduler
    App-->>App: Service Ready (Port 8000)
```

### Phase 2: Scheduled Job Execution (Every 2-6 minutes)

```mermaid
sequenceDiagram
    participant Sched as APScheduler
    participant Job as Job Executor
    participant GPS as Mock GPS Provider
    participant Norm as Normalization Service
    participant TR as Telemetry Repository
    participant DB as MongoDB Atlas

    Sched->>Job: Trigger Job (e.g., Position Collection)
    Job->>Job: Load VIN List from Parameters
    
    loop For Each VIN (Concurrent Processing)
        Job->>GPS: get_vehicle_data_by_vin(vin, report_type)
        
        alt VIN in Mock Data
            GPS->>GPS: Return Static Mock Response
        else VIN Not in Mock Data
            GPS->>GPS: Generate Random GPS Data
        end
        
        GPS-->>Job: Raw GPS Response (JSON)
        
        Job->>Norm: normalize_report(report_type, raw_data)
        Norm->>Norm: Parse & Transform to Canonical Model
        Norm-->>Job: VehicleTelemetry Objects
        
        Job->>TR: insert_many(telemetry_records)
        TR->>DB: Bulk Insert into vehicle_telemetry
        DB-->>TR: Insert Confirmation
        TR-->>Job: Success/Failure Count
    end
    
    Job->>Job: Calculate Job Metrics
    Job->>TR: insert_job_log(execution_summary)
    TR->>DB: Insert into job_execution_logs
    
    Job-->>Sched: Job Completed (Success/Failure)
```

### Phase 3: API Request Handling

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as FastAPI App
    participant DB as MongoDB Atlas
    participant Sched as APScheduler

    Client->>API: GET /health
    API->>DB: Ping MongoDB
    API->>Sched: Check Scheduler Status
    API-->>Client: Health Status Response
    
    Client->>API: GET /api/v1/jobs/
    API->>Sched: Get Active Jobs
    Sched-->>API: Job List
    API-->>Client: Jobs Response
    
    Client->>API: GET /api/v1/jobs/statistics
    API->>DB: Aggregate Job Execution Data
    DB-->>API: Statistics Data
    API-->>Client: Statistics Response
```

## 🗄️ Database Schema

### Collection: `vehicles`

**Purpose:** Master data for vehicles being tracked

```json
{
  "_id": ObjectId("..."),
  "vin": "3KPA24BC4NE453663",
  "vehicle_name": "1008",
  "make": "Kia",
  "model": "Rio",
  "year": 2022,
  "license_plate": "MEX-1008",
  "fleet_id": "FLEET-001",
  "is_active": true,
  "created_at": "2024-01-07T10:00:00.000Z",
  "updated_at": "2024-01-07T10:00:00.000Z"
}
```

**Indexes:**
- `vin` (unique)
- `vehicle_name`
- `is_active`

**Sample Query:**
```javascript
// Get all active VINs
db.vehicles.find({is_active: true}, {vin: 1, _id: 0})

// Count vehicles by fleet
db.vehicles.aggregate([
  {$group: {_id: "$fleet_id", count: {$sum: 1}}}
])
```

### Collection: `vehicle_telemetry`

**Purpose:** Normalized GPS telemetry data from all report types

```json
{
  "_id": ObjectId("..."),
  "vin": "3KPA24BC4NE453663",
  "vehicle_name": "1008",
  
  // Location Data (lastPos reports)
  "location": {
    "latitude": 19.340975,
    "longitude": -99.121057,
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  
  // Speed Data (speed reports)
  "speed": {
    "value": 65.5,
    "unit": "km/h",
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  
  // Odometer Data (odometer reports)
  "odometer": {
    "value": 70870,
    "unit": "km",
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  
  // Vehicle Status
  "engine_status": 0,  // 0=OFF, 1=ON
  "ignition_status": 1, // 0=OFF, 1=ON
  
  // Trip Data (recorridos reports)
  "trips": {
    "count": 14,
    "total_duration_seconds": 13902,
    "total_distance_km": 59.0
  },
  
  // Parking Events (estacionamientos reports)
  "parking_events": [
    {
      "duration_hours": 14.0,
      "location": null,
      "start_time": null,
      "end_time": null
    }
  ],
  
  // Consumption Data (consumos reports)
  "consumption": {
    "distance_km": null,
    "time_on_movement_seconds": null,
    "calculated_consumption": null,
    "unit": "L/100km"
  },
  
  // Hardware Health (voltage reports)
  "voltage": {
    "value": 12.4,
    "unit": "V",
    "timestamp": "2024-08-30T12:40:50.000Z",
    "is_healthy": true
  },
  
  // Event Classification
  "event_type": "position_update",
  
  // Ingestion Metadata
  "metadata": {
    "provider_name": "mock_gps_provider",
    "report_type": "lastPos",
    "ingestion_timestamp": "2024-01-07T10:05:00.000Z",
    "ingestion_status": "success",
    "data_quality": "high",
    "raw_data": {
      "parsedData": {
        "1008": {
          "VIN": "3KPA24BC4NE453663",
          "y": 19.340975,
          "x": -99.121057,
          "t": "2024-08-30T12:40:50.000"
        }
      }
    },
    "error_message": null,
    "retry_count": 0
  },
  
  // Timestamps
  "recorded_at": "2024-08-30T12:40:50.000Z",
  "created_at": "2024-01-07T10:05:00.000Z",
  "updated_at": "2024-01-07T10:05:00.000Z"
}
```

**Indexes:**
- `(vin, recorded_at)` - Vehicle queries
- `(metadata.report_type, recorded_at)` - Report type queries
- `(event_type, recorded_at)` - Event queries
- TTL index on `created_at` (90 days retention)

**Sample Queries:**
```javascript
// Get latest position for a vehicle
db.vehicle_telemetry.findOne(
  {
    vin: "3KPA24BC4NE453663",
    "metadata.report_type": "lastPos"
  },
  {sort: {recorded_at: -1}}
)

// Count telemetry by report type
db.vehicle_telemetry.aggregate([
  {$group: {_id: "$metadata.report_type", count: {$sum: 1}}}
])

// Get speed violations (>80 km/h)
db.vehicle_telemetry.find({
  "speed.value": {$gt: 80},
  "metadata.report_type": "speed"
})
```

### Collection: `job_execution_logs`

**Purpose:** Track scheduled job execution metrics and performance

```json
{
  "_id": ObjectId("..."),
  "job_name": "vehicle_position_collection",
  "job_type": "position_collection",
  "start_time": "2024-01-07T10:05:00.000Z",
  "end_time": "2024-01-07T10:05:45.000Z",
  "status": "success",
  "vehicles_processed": 105,
  "vehicles_succeeded": 103,
  "vehicles_failed": 2,
  "error_summary": {
    "total_errors": 2,
    "errors": [
      {
        "vin": "ABC123DEF456GHI78",
        "error": "Connection timeout"
      }
    ]
  },
  "execution_metadata": {
    "speed_violations": 5,
    "low_voltage_alerts": 2
  }
}
```

**Indexes:**
- `(job_name, start_time)`
- TTL index on `start_time` (30 days retention)

**Sample Queries:**
```javascript
// Get job success rates
db.job_execution_logs.aggregate([
  {
    $group: {
      _id: "$job_name",
      avg_success_rate: {
        $avg: {
          $divide: ["$vehicles_succeeded", "$vehicles_processed"]
        }
      },
      total_executions: {$sum: 1}
    }
  }
])
```

## 🔌 API Schema

### GPS Provider Interface

**Mock GPS Provider API Simulation:**

```typescript
interface IGPSProvider {
  // Authentication
  authenticate(): Promise<boolean>
  
  // Data Retrieval Methods
  get_vehicle_data_by_vin(vin: string, report_type: ReportType): Promise<GPSResponse>
  get_bulk_report(report_type: ReportType): Promise<GPSResponse>
  get_report_by_date(report_type: ReportType, date: Date): Promise<GPSResponse>
  get_report_by_time_range(report_type: ReportType, vin: string, start: Date, end: Date): Promise<GPSResponse>
  get_report_by_name(report_type: ReportType, vehicle_name: string): Promise<GPSResponse>
  
  // Health Check
  health_check(): Promise<boolean>
  get_provider_name(): string
}
```

**GPS Response Schema:**

```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "y": 19.340975,
      "x": -99.121057,
      "t": "2024-08-30T12:40:50.000"
    },
    "1009": {
      "VIN": "3KPA24BC2NE460675",
      "y": 19.365197,
      "x": -99.265575,
      "t": "2024-08-01T13:55:27.000"
    }
  }
}
```

### Report Type Schemas

#### 1. Position Reports (`lastPos`)

**Request:**
```http
POST /mock-gps-api/lastPos
Content-Type: application/json

{
  "vin": "3KPA24BC4NE453663"
}
```

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "y": 19.340975,
      "x": -99.121057,
      "t": "2024-08-30T12:40:50.000"
    }
  }
}
```

#### 2. Odometer Reports (`odometros`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "odo": "70870 km"
    }
  }
}
```

#### 3. Engine Status Reports (`engineStatus`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "engineStatus": "0"
    }
  }
}
```

#### 4. Speed Reports (`speed`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "date": "2024-08-30T12:47:58.000",
      "speed": "65 km/h"
    }
  }
}
```

#### 5. Ignition Reports (`ignition`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "date": "2024-08-30T12:39:50.000",
      "ignition": "1"
    }
  }
}
```

#### 6. Trip Reports (`recorridos`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "count": "14",
      "totalDuration": "3:51:42",
      "totalKm": "59 km"
    }
  }
}
```

#### 7. Parking Reports (`estacionamientos`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "events": [
        {
          "duration": "14",
          "t": "noData",
          "y": "checkDayBefore",
          "x": "checkDayBefore"
        }
      ]
    }
  }
}
```

#### 8. Consumption Reports (`consumos`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "km": "",
      "timeOnMovement": "",
      "calculatedConsumption": "",
      "data": "noData"
    }
  }
}
```

#### 9. Voltage Reports (`voltage`)

**Response:**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "voltage": "12.4 V",
      "timestamp": "2024-08-30T12:40:50.000"
    }
  }
}
```

## 🔄 Data Transformation Flow

### Raw GPS Data → Canonical Model

```mermaid
graph TD
    A[Raw GPS Response] --> B{Report Type}
    
    B -->|lastPos| C[Position Normalization]
    B -->|odometros| D[Odometer Normalization]
    B -->|engineStatus| E[Engine Status Normalization]
    B -->|speed| F[Speed Normalization]
    B -->|ignition| G[Ignition Normalization]
    B -->|recorridos| H[Trip Normalization]
    B -->|estacionamientos| I[Parking Normalization]
    B -->|consumos| J[Consumption Normalization]
    B -->|voltage| K[Voltage Normalization]
    
    C --> L[VehicleTelemetry Object]
    D --> L
    E --> L
    F --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[Add Metadata]
    M --> N[Validate Schema]
    N --> O[Store in MongoDB]
```

### Normalization Examples

**Input (Raw GPS):**
```json
{
  "parsedData": {
    "1008": {
      "VIN": "3KPA24BC4NE453663",
      "y": 19.340975,
      "x": -99.121057,
      "t": "2024-08-30T12:40:50.000"
    }
  }
}
```

**Output (Canonical Model):**
```json
{
  "vin": "3KPA24BC4NE453663",
  "vehicle_name": "1008",
  "location": {
    "latitude": 19.340975,
    "longitude": -99.121057,
    "timestamp": "2024-08-30T12:40:50.000Z"
  },
  "event_type": "position_update",
  "metadata": {
    "provider_name": "mock_gps_provider",
    "report_type": "lastPos",
    "ingestion_timestamp": "2024-01-07T10:05:00.000Z",
    "ingestion_status": "success",
    "data_quality": "high",
    "raw_data": { /* original response */ }
  },
  "recorded_at": "2024-08-30T12:40:50.000Z",
  "created_at": "2024-01-07T10:05:00.000Z"
}
```

## 🕐 Job Scheduling Schema

### Cron Job Configuration

```yaml
Jobs:
  vehicle_position_collection:
    schedule: "*/2 * * * *"  # Every 2 minutes
    report_type: "lastPos"
    description: "Collect GPS positions"
    
  odometer_collection:
    schedule: "*/3 * * * *"  # Every 3 minutes
    report_type: "odometros"
    description: "Collect odometer readings"
    
  engine_status_monitoring:
    schedule: "*/4 * * * *"  # Every 4 minutes
    report_type: "engineStatus"
    description: "Monitor engine status"
    
  speed_monitoring:
    schedule: "*/2 * * * *"  # Every 2 minutes
    report_type: "speed"
    description: "Monitor vehicle speeds"
    
  ignition_monitoring:
    schedule: "*/5 * * * *"  # Every 5 minutes
    report_type: "ignition"
    description: "Monitor ignition status"
    
  voltage_health_check:
    schedule: "*/6 * * * *"  # Every 6 minutes
    report_type: "voltage"
    description: "Check GPS device voltage"
```

### Job Execution Flow

```mermaid
sequenceDiagram
    participant Cron as Cron Trigger
    participant Job as Job Function
    participant GPS as GPS Provider
    participant Norm as Normalizer
    participant DB as MongoDB

    Cron->>Job: Execute Job (with VIN list)
    
    loop For Each VIN (Concurrent)
        Job->>GPS: Request GPS Data
        GPS-->>Job: Raw GPS Response
        
        Job->>Norm: Normalize Data
        Norm-->>Job: Canonical Objects
        
        Job->>DB: Store Telemetry
        DB-->>Job: Confirm Storage
    end
    
    Job->>Job: Calculate Metrics
    Job->>DB: Store Job Log
    Job-->>Cron: Job Complete
```

## 🔧 Configuration Schema

### Environment Variables

```bash
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# MongoDB Atlas
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=gpsdevice
MONGODB_DB_NAME=gps_telemetry
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_POOL_SIZE=100

# GPS Provider
GPS_PROVIDER_TYPE=mock
GPS_API_BASE_URL=http://mock-gps-api:3000
GPS_API_TIMEOUT=30
GPS_API_MAX_RETRIES=3

# Concurrency
MAX_CONCURRENT_REQUESTS=10
BATCH_SIZE=50
RATE_LIMIT_REQUESTS_PER_SECOND=5.0

# Job Schedules (Cron)
JOB_VEHICLE_POSITION_CRON=*/2 * * * *
JOB_ODOMETER_CRON=*/3 * * * *
JOB_ENGINE_STATUS_CRON=*/4 * * * *
JOB_SPEED_MONITORING_CRON=*/2 * * * *
JOB_IGNITION_CRON=*/5 * * * *
JOB_VOLTAGE_HEALTH_CRON=*/6 * * * *

# Data Retention
TELEMETRY_RETENTION_DAYS=90
JOB_LOG_RETENTION_DAYS=30
```

## 📊 Performance Metrics

### System Throughput

```
Vehicles: 100+
Job Frequency: Every 2-6 minutes
Concurrent Requests: 10
Batch Size: 50 vehicles

Expected Throughput:
- Position Data: ~50 records/minute
- Odometer Data: ~33 records/minute  
- Engine Status: ~25 records/minute
- Speed Data: ~50 records/minute
- Ignition Data: ~20 records/minute
- Voltage Data: ~17 records/minute

Total: ~195 telemetry records/minute
Daily: ~280,800 records/day
```

### Database Growth

```
Per Vehicle Per Day:
- Position: 720 records (every 2 min)
- Odometer: 480 records (every 3 min)
- Engine: 360 records (every 4 min)
- Speed: 720 records (every 2 min)
- Ignition: 288 records (every 5 min)
- Voltage: 240 records (every 6 min)

Total per vehicle: 2,808 records/day
For 100 vehicles: 280,800 records/day
Monthly (30 days): 8,424,000 records
```

## 🔐 Security Schema

### Data Protection

```yaml
Authentication:
  - GPS Provider: Username/Password
  - MongoDB: Connection String with credentials
  - API: No authentication (internal service)

Data Encryption:
  - In Transit: HTTPS/TLS for all API calls
  - At Rest: MongoDB Atlas encryption

Access Control:
  - Container: Non-root user (appuser:1000)
  - Database: Dedicated service account
  - Network: Internal Docker network

Data Retention:
  - Telemetry: 90 days (TTL index)
  - Job Logs: 30 days (TTL index)
  - Automatic cleanup via MongoDB TTL
```

## 🚀 Deployment Schema

### Docker Container Structure

```
Container: gps-data-collection-service
├── Application Code (/app)
│   ├── app/                    # FastAPI application
│   ├── scripts/               # Utility scripts
│   └── requirements.txt       # Python dependencies
├── Runtime Environment
│   ├── Python 3.11
│   ├── FastAPI + Uvicorn
│   ├── MongoDB Motor Driver
│   └── APScheduler
└── Configuration
    ├── Environment Variables
    ├── Health Checks
    └── Resource Limits (2GB RAM, 2 CPU)
```

### Service Dependencies

```mermaid
graph TD
    A[GPS Service Container] --> B[MongoDB Atlas]
    A --> C[Mock GPS Provider]
    A --> D[Docker Network]
    
    B --> E[Internet Connection]
    C --> F[Static Mock Data]
    D --> G[Port 8000 Mapping]
    
    A --> H[Health Checks]
    A --> I[Log Aggregation]
    A --> J[Metrics Collection]
```

## 📈 Monitoring Schema

### Health Check Endpoints

```http
GET /health
Response: {
  "status": "healthy",
  "service": "GPS Data Collection Service",
  "components": {
    "mongodb": "healthy",
    "scheduler": "healthy"
  }
}

GET /api/v1/jobs/statistics
Response: {
  "statistics": [
    {
      "job_name": "vehicle_position_collection",
      "total_executions": 150,
      "successful_executions": 148,
      "failed_executions": 2,
      "avg_duration_seconds": 45.2,
      "avg_success_rate": 98.67
    }
  ]
}
```

### Log Schema

```json
{
  "timestamp": "2024-01-07T10:05:00.000Z",
  "level": "INFO",
  "service": "GPS Data Collection Service",
  "environment": "development",
  "message": "Job completed successfully",
  "job_name": "vehicle_position_collection",
  "success_rate": 98.5,
  "duration_seconds": 45.2,
  "vehicles_processed": 105,
  "vehicles_succeeded": 103,
  "vehicles_failed": 2
}
```

## 🔄 Error Handling Schema

### Exception Hierarchy

```python
GPSDataCollectionError (Base)
├── GPSProviderError
│   ├── GPSProviderTimeout
│   └── GPSProviderAuthenticationError
├── DataNormalizationError
├── RepositoryError
├── JobExecutionError
└── ConfigurationError
```

### Error Response Format

```json
{
  "error": {
    "type": "GPSProviderTimeout",
    "message": "Request to GPS provider timed out after 30s",
    "details": {
      "vin": "3KPA24BC4NE453663",
      "report_type": "lastPos",
      "timeout_seconds": 30
    },
    "timestamp": "2024-01-07T10:05:00.000Z"
  }
}
```

This comprehensive schema document provides a complete technical reference for understanding the GPS data collection service architecture, data flows, and all system interactions.