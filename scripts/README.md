# Scripts Directory

## Mock Data Seeding

### seed_mock_vehicles.py

Seeds the MongoDB database with mock vehicle data for testing and development.

**Purpose:**
- Populates the `vehicles` collection with 5 mock vehicles
- Each vehicle has a VIN that matches the mock GPS provider's data
- Enables the scheduler to fetch real vehicle IDs from the database

**Usage:**

```bash
# Run the seeding script
python scripts/seed_mock_vehicles.py
```

**Mock Vehicles:**

| VIN | Vehicle Name | Make | Model | Year | License Plate | Fleet |
|-----|--------------|------|-------|------|---------------|-------|
| LSGHD52H9ND045496 | 1006 | Hyundai | Accent | 2022 | MEX-1006 | FLEET-001 |
| 3KPA24BC4NE453663 | 1008 | Kia | Rio | 2022 | MEX-1008 | FLEET-001 |
| 3KPA24BC2NE460675 | 1009 | Kia | Rio | 2022 | MEX-1009 | FLEET-001 |
| MEX5B2605NT017117 | 1010 | Mazda | CX-5 | 2023 | MEX-1010 | FLEET-002 |
| MEX5B2602NT012229 | 1011 | Mazda | CX-5 | 2023 | MEX-1011 | FLEET-002 |

**What Happens:**

1. Script connects to MongoDB Atlas
2. Creates `vehicles` collection with indexes
3. Inserts 5 mock vehicles
4. Verifies insertion
5. Displays all active VINs

**After Seeding:**

The application will:
1. Fetch VINs from the `vehicles` collection on startup
2. Use those VINs to query the mock GPS provider
3. Store normalized telemetry data in `vehicle_telemetry` collection

**Data Flow:**

```
MongoDB (vehicles) → Application → Mock GPS Provider → Normalization → MongoDB (vehicle_telemetry)
     ↓                    ↓                ↓                  ↓                    ↓
  [VINs]           [Fetch VINs]    [Get GPS Data]    [Normalize]         [Store Results]
```

## Other Scripts

### run_job_manually.py

Manually trigger a specific job for testing purposes.

```bash
python scripts/run_job_manually.py
```

### run_dev.sh

Development server startup script with hot reload.

```bash
bash scripts/run_dev.sh
```
