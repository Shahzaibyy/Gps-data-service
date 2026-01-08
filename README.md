# GPS Data Collection Microservice

Enterprise-grade FastAPI microservice for collecting and normalizing GPS IoT device data from vehicles.

## Features

- ✅ **Clean Architecture** - Domain-driven design with SOLID principles
- ✅ **Async I/O** - Full async/await for high performance
- ✅ **MongoDB Atlas** - Cloud-native database with connection pooling
- ✅ **Scheduled Jobs** - APScheduler for cron-based data collection
- ✅ **Mock GPS Provider** - Development-ready mock implementation
- ✅ **Data Normalization** - Canonical domain models for all GPS reports
- ✅ **Retry Logic** - Exponential backoff with rate limiting
- ✅ **Observability** - Structured logging and health checks
- ✅ **Dockerized** - Production-ready container setup

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼────┐            ┌───────▼──────┐
│ Scheduler│          │  API Endpoints│
│(APScheduler)│       │  /health /jobs│
└───┬────┘            └──────────────┘
    │
┌───▼─────────────┐
│  Scheduled Jobs  │
│  - Position      │
│  - Odometer      │
│  - Engine Status │
└───┬─────────────┘
    │
┌───▼──────────────┐
│  GPS Provider    │
│  (Mock/Real)     │
└───┬──────────────┘
    │
┌───▼──────────────┐
│ Normalization    │
│    Service       │
└───┬──────────────┘
    │
┌───▼──────────────┐
│  MongoDB Atlas   │
│   Repository     │
└──────────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Poetry** (for dependency management)
- **MongoDB Atlas Account** (already configured)
- **Docker & Docker Compose** (optional)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd gps-data-collection-service
```

### 2. Install Dependencies

```bash
# Using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# MongoDB URL is already configured for your Atlas cluster
```

### 4. Run Locally

```bash
# Using Poetry
poetry run python -m app.main

# Or directly
python -m app.main
```

The service will start on `http://localhost:8000`

### 5. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f gps-service

# Stop services
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t gps-data-collection:latest .

# Run container
docker run -d \
  --name gps-service \
  -p 8000:8000 \
  --env-file .env \
  gps-data-collection:latest
```

## MongoDB Atlas Configuration

Your MongoDB Atlas cluster is already configured in the `.env` file:

```
MONGODB_URL=""
MONGODB_DB_NAME="gps_telemetry"
```

### Database Structure

The service creates the following collections:

- **vehicle_telemetry** - Normalized telemetry data
- **job_execution_logs** - Job execution history
- **apscheduler_jobs** - Scheduled jobs state

### Indexes

Indexes are automatically created on startup:
- `(vin, recorded_at)` - For vehicle queries
- `(metadata.report_type, recorded_at)` - For report type queries
- `(event_type, recorded_at)` - For event queries
- TTL indexes for data retention

## API Endpoints

### Health & Monitoring

```bash
# Comprehensive health check
GET /health

# Liveness probe (Kubernetes)
GET /api/v1/health/liveness

# Readiness probe (Kubernetes)
GET /api/v1/health/readiness
```

### Job Management

```bash
# List all scheduled jobs
GET /api/v1/jobs/

# Pause a job
POST /api/v1/jobs/{job_id}/pause

# Resume a job
POST /api/v1/jobs/{job_id}/resume

# Get job execution history
GET /api/v1/jobs/{job_name}/history?limit=10

# Get job statistics
GET /api/v1/jobs/statistics
```

## Scheduled Jobs

Jobs are configured via environment variables:

| Job | Schedule | Description |
|-----|----------|-------------|
| Vehicle Position | `*/5 * * * *` | Collect GPS position every 5 minutes |
| Odometer | `0 */6 * * *` | Collect odometer readings every 6 hours |
| Engine Status | `*/10 * * * *` | Monitor engine status every 10 minutes |
| Speed Monitoring | `*/5 * * * *` | Track vehicle speed every 5 minutes |
| Ignition Status | `*/15 * * * *` | Check ignition every 15 minutes |
| Voltage Health | `0 0 * * *` | Check battery voltage daily |

### Customizing Schedules

Edit cron expressions in `.env`:

```bash
# Every 2 minutes
JOB_VEHICLE_POSITION_CRON="*/2 * * * *"

# Every hour at minute 30
JOB_ODOMETER_CRON="30 * * * *"
```

## Configuration

### Key Environment Variables

```bash
# Application
ENVIRONMENT=development  # development | staging | production
DEBUG=true
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR

# GPS Provider
GPS_PROVIDER_TYPE=mock   # mock | real

# Concurrency
MAX_CONCURRENT_REQUESTS=10    # Simultaneous API calls
BATCH_SIZE=50                 # Vehicles per batch
RATE_LIMIT_REQUESTS_PER_SECOND=5.0

# Data Retention
TELEMETRY_RETENTION_DAYS=90   # Auto-delete after 90 days
JOB_LOG_RETENTION_DAYS=30     # Keep logs for 30 days
```

## Development

### Project Structure

```
gps-data-collection-service/
├── app/
│   ├── api/                    # API layer
│   │   └── v1/
│   │       ├── endpoints/      # REST endpoints
│   │       └── schemas/        # Pydantic schemas
│   ├── application/            # Application layer
│   │   ├── jobs/              # Scheduled jobs
│   │   └── services/          # Business logic
│   ├── core/                   # Core utilities
│   │   ├── config.py          # Configuration
│   │   ├── dependencies.py    # DI container
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── logging.py         # Logging setup
│   ├── domain/                 # Domain layer
│   │   ├── interfaces/        # Abstract interfaces
│   │   └── models/            # Domain models
│   ├── infrastructure/         # Infrastructure layer
│   │   ├── database/          # MongoDB repositories
│   │   ├── gps_providers/     # GPS implementations
│   │   └── http/              # HTTP client
│   ├── scheduler/             # Job scheduling
│   └── main.py                # Application entry point
├── tests/                      # Test suite
├── .env                        # Environment config
├── docker-compose.yml         # Docker Compose
├── Dockerfile                 # Docker image
└── pyproject.toml             # Dependencies
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test
poetry run pytest tests/unit/test_normalization.py
```

### Code Quality

```bash
# Format code
poetry run black app/

# Lint code
poetry run ruff check app/

# Type checking
poetry run mypy app/
```

## Monitoring & Observability

### Logs

Logs are structured JSON in production:

```json
{
  "timestamp": "2024-01-07T10:30:00Z",
  "level": "INFO",
  "service": "GPS Data Collection Service",
  "environment": "production",
  "message": "Job completed successfully",
  "job_name": "vehicle_position_collection",
  "success_rate": 98.5,
  "duration_seconds": 45.2
}
```

### Metrics

Ready for Prometheus integration:
- Job execution duration
- Success/failure rates
- API request latency
- MongoDB connection pool stats

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Kubernetes probes
curl http://localhost:8000/api/v1/health/liveness
curl http://localhost:8000/api/v1/health/readiness
```

## Switching to Real GPS Provider

1. Implement `RealGPSProvider` class:

```python
# app/infrastructure/gps_providers/real_provider.py
class RealGPSProvider(IGPSProvider):
    async def authenticate(self) -> bool:
        # Implement real authentication
        pass
    
    async def get_vehicle_data_by_vin(self, vin: str, report_type: ReportType):
        # Implement real API calls
        pass
```

2. Update configuration:

```bash
GPS_PROVIDER_TYPE=real
GPS_API_BASE_URL=https://your-gps-api.com
GPS_API_USERNAME=your_username
GPS_API_PASSWORD=your_password
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('your-mongodb-url'); client.admin.command('ping'); print('Connected!')"

# Check network access in MongoDB Atlas
# 1. Go to Atlas Dashboard
# 2. Network Access > Add IP Address
# 3. Allow access from your IP or 0.0.0.0/0 (development only)
```

### Job Not Running

```bash
# Check job status
curl http://localhost:8000/api/v1/jobs/

# View job logs
docker-compose logs -f gps-service | grep "vehicle_position"

# Check scheduler is running
curl http://localhost:8000/health | jq '.components.scheduler'
```

### High Memory Usage

Adjust concurrency settings in `.env`:

```bash
MAX_CONCURRENT_REQUESTS=5  # Reduce from 10
BATCH_SIZE=25             # Reduce from 50
```

## Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Use strong MongoDB credentials
- [ ] Configure proper MongoDB network access
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Implement real GPS provider
- [ ] Set up CI/CD pipeline
- [ ] Configure resource limits
- [ ] Enable HTTPS/TLS
- [ ] Set up log aggregation
- [ ] Configure secrets management

## Support

For issues, questions, or contributions, please contact the development team.

## License

Proprietary - Internal Use Only