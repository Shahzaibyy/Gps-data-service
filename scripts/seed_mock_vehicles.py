"""
Seed script to populate MongoDB with mock vehicle data.
Run this script to initialize the database with test vehicles.

Usage:
    python scripts/seed_mock_vehicles.py
    python scripts/seed_mock_vehicles.py --count 100
"""
import asyncio
import sys
import random
import string
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.models.vehicle import Vehicle
from app.infrastructure.database.mongodb import get_mongodb_manager
from app.infrastructure.database.repositories.vehicle_repository import VehicleRepository
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def generate_vin():
    """Generate a random 17-character VIN."""
    # VIN format: WMI (3) + VDS (6) + VIS (8) = 17 characters
    # Exclude I, O, Q to avoid confusion
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('I', '').replace('O', '').replace('Q', '')
    
    return ''.join(random.choices(chars, k=17))


def generate_license_plate():
    """Generate a random license plate."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}-{numbers}"


def generate_random_vehicles(count: int) -> list[Vehicle]:
    """Generate random vehicle data."""
    
    # Vehicle makes and models
    vehicle_data = [
        ("Toyota", ["Camry", "Corolla", "RAV4", "Prius", "Highlander"]),
        ("Honda", ["Civic", "Accord", "CR-V", "Pilot", "Fit"]),
        ("Ford", ["F-150", "Escape", "Explorer", "Focus", "Mustang"]),
        ("Chevrolet", ["Silverado", "Equinox", "Malibu", "Tahoe", "Cruze"]),
        ("Nissan", ["Altima", "Sentra", "Rogue", "Pathfinder", "Versa"]),
        ("Hyundai", ["Elantra", "Sonata", "Tucson", "Santa Fe", "Accent"]),
        ("Kia", ["Optima", "Sorento", "Sportage", "Rio", "Soul"]),
        ("Mazda", ["CX-5", "Mazda3", "CX-9", "Mazda6", "CX-3"]),
        ("Subaru", ["Outback", "Forester", "Impreza", "Legacy", "Crosstrek"]),
        ("Volkswagen", ["Jetta", "Passat", "Tiguan", "Atlas", "Golf"])
    ]
    
    # Fleet IDs
    fleet_ids = [f"FLEET-{str(i).zfill(3)}" for i in range(1, 21)]  # FLEET-001 to FLEET-020
    
    vehicles = []
    
    for i in range(count):
        make, models = random.choice(vehicle_data)
        model = random.choice(models)
        year = random.randint(2018, 2024)
        fleet_id = random.choice(fleet_ids)
        
        vehicle = Vehicle(
            vin=generate_vin(),
            vehicle_name=f"{1000 + i}",  # 1000, 1001, 1002, etc.
            make=make,
            model=model,
            year=year,
            license_plate=generate_license_plate(),
            fleet_id=fleet_id,
            is_active=random.choice([True, True, True, False])  # 75% active
        )
        
        vehicles.append(vehicle)
    
    return vehicles


# Original 5 vehicles that match GPS provider mock data
ORIGINAL_MOCK_VEHICLES = [
    Vehicle(
        vin="LSGHD52H9ND045496",
        vehicle_name="1006",
        make="Hyundai",
        model="Accent",
        year=2022,
        license_plate="MEX-1006",
        fleet_id="FLEET-001",
        is_active=True
    ),
    Vehicle(
        vin="3KPA24BC4NE453663",
        vehicle_name="1008",
        make="Kia",
        model="Rio",
        year=2022,
        license_plate="MEX-1008",
        fleet_id="FLEET-001",
        is_active=True
    ),
    Vehicle(
        vin="3KPA24BC2NE460675",
        vehicle_name="1009",
        make="Kia",
        model="Rio",
        year=2022,
        license_plate="MEX-1009",
        fleet_id="FLEET-001",
        is_active=True
    ),
    Vehicle(
        vin="MEX5B2605NT017117",
        vehicle_name="1010",
        make="Mazda",
        model="CX-5",
        year=2023,
        license_plate="MEX-1010",
        fleet_id="FLEET-002",
        is_active=True
    ),
    Vehicle(
        vin="MEX5B2602NT012229",
        vehicle_name="1011",
        make="Mazda",
        model="CX-5",
        year=2023,
        license_plate="MEX-1011",
        fleet_id="FLEET-002",
        is_active=True
    ),
]


async def seed_vehicles():
    """Seed the database with mock vehicle data."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Seed mock vehicle data')
    parser.add_argument('--count', type=int, default=100, help='Number of vehicles to generate (default: 100)')
    parser.add_argument('--include-original', action='store_true', default=True, help='Include original 5 vehicles')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Starting Mock Vehicle Data Seeding")
    logger.info(f"Generating {args.count} random vehicles")
    if args.include_original:
        logger.info("Including 5 original vehicles (GPS provider compatible)")
    logger.info("=" * 60)
    
    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        mongodb_manager = get_mongodb_manager()
        db = await mongodb_manager.connect()
        
        if db is None:
            logger.error("Failed to connect to MongoDB")
            return False
        
        logger.info("✓ MongoDB connected")
        
        # Initialize repository
        vehicle_repo = VehicleRepository(db)
        await vehicle_repo.ensure_indexes()
        logger.info("✓ Vehicle repository initialized")
        
        # Check existing vehicles
        existing_count = await vehicle_repo.count_vehicles(active_only=False)
        logger.info(f"Existing vehicles in database: {existing_count}")
        
        if existing_count > 0:
            logger.warning("Database already contains vehicles")
            response = input(f"Do you want to add {args.count} more vehicles? (y/n): ")
            if response.lower() != 'y':
                logger.info("Seeding cancelled by user")
                return False
        
        # Generate vehicles
        logger.info(f"Generating {args.count} random vehicles...")
        vehicles_to_insert = []
        
        # Add original vehicles if requested
        if args.include_original:
            vehicles_to_insert.extend(ORIGINAL_MOCK_VEHICLES)
            logger.info("Added 5 original vehicles (GPS provider compatible)")
        
        # Generate random vehicles
        random_vehicles = generate_random_vehicles(args.count)
        vehicles_to_insert.extend(random_vehicles)
        
        total_vehicles = len(vehicles_to_insert)
        logger.info(f"Total vehicles to insert: {total_vehicles}")
        
        # Insert vehicles in batches
        batch_size = 50
        inserted_count = 0
        skipped_count = 0
        
        for i in range(0, total_vehicles, batch_size):
            batch = vehicles_to_insert[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_vehicles + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} vehicles)...")
            
            try:
                await vehicle_repo.insert_many(batch)
                inserted_count += len(batch)
                logger.info(f"  ✓ Batch {batch_num} inserted successfully")
            except Exception as e:
                # Try individual inserts for this batch
                logger.warning(f"  ⚠ Batch {batch_num} failed, trying individual inserts...")
                for vehicle in batch:
                    try:
                        await vehicle_repo.insert_one(vehicle)
                        inserted_count += 1
                    except Exception as ve:
                        skipped_count += 1
                        logger.warning(f"    ⚠ Skipped: {vehicle.vin} - {str(ve)}")
        
        logger.info("=" * 60)
        logger.info(f"Seeding Complete!")
        logger.info(f"  Inserted: {inserted_count}")
        logger.info(f"  Skipped:  {skipped_count}")
        logger.info(f"  Total:    {total_vehicles}")
        logger.info("=" * 60)
        
        # Verify
        final_count = await vehicle_repo.count_vehicles(active_only=False)
        active_count = await vehicle_repo.count_vehicles(active_only=True)
        
        logger.info(f"\nDatabase Summary:")
        logger.info(f"  Total vehicles: {final_count}")
        logger.info(f"  Active vehicles: {active_count}")
        logger.info(f"  Inactive vehicles: {final_count - active_count}")
        
        # Show sample VINs
        sample_vins = await vehicle_repo.get_all_vins(active_only=True)
        logger.info(f"\nSample active VINs (first 10):")
        for vin in sample_vins[:10]:
            logger.info(f"  - {vin}")
        
        if len(sample_vins) > 10:
            logger.info(f"  ... and {len(sample_vins) - 10} more")
        
        # Disconnect
        await mongodb_manager.disconnect()
        logger.info("\n✓ MongoDB disconnected")
        
        return True
        
    except Exception as e:
        logger.error("Seeding failed", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(seed_vehicles())
    sys.exit(0 if success else 1)
