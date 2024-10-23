from datetime import date, datetime

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import VehicleAllocation
from bson import ObjectId
from typing import Optional, List
import logging

# Create an allocation
logging.basicConfig(level=logging.INFO)

async def create_allocation(allocation: VehicleAllocation, db: AsyncIOMotorDatabase):
    # Check if vehicle is already allocated for the given date
    existing_allocation = await db["allocations"].find_one({
        "vehicle_id": allocation.vehicle_id,
        "allocation_date": allocation.allocation_date.isoformat()  # Use ISO format
    })
    if existing_allocation:
        raise ValueError(f"Vehicle already allocated for {allocation.allocation_date}")

    allocation_dict = allocation.to_mongo()  # Convert to dict for MongoDB
    result = await db["allocations"].insert_one(allocation_dict)
    return str(result.inserted_id)

# Update an allocation
async def update_allocation(allocation_id: str, update_data: dict, db: AsyncIOMotorDatabase):
    result = await db["allocations"].update_one({"_id": ObjectId(allocation_id)}, {"$set": update_data})
    return result.modified_count

# Delete an allocation
async def delete_allocation(allocation_id, db):
    today_datetime = datetime.combine(date.today(), datetime.min.time())
    logging.info(f"Attempting to delete allocation with ID: {allocation_id}")

    if not ObjectId.is_valid(allocation_id):
        logging.error("Invalid allocation ID format.")
        raise HTTPException(status_code=400, detail="Invalid allocation ID")

    result = await db["allocations"].delete_one({
        "_id": ObjectId(allocation_id),
        "allocation_date": {"$gte": today_datetime}
    })

    logging.info(f"Deleted count: {result.deleted_count}")
    return result.deleted_count

# Fetch allocation history
async def get_allocation_history(employee_id: Optional[str], vehicle_id: Optional[str], db: AsyncIOMotorDatabase) -> \
List[dict]:
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if vehicle_id:
        query["vehicle_id"] = vehicle_id

    # Fetch allocations and convert ObjectId to string
    allocations = await db["allocations"].find(query).to_list(length=None)

    # Map the results to include 'id' instead of '_id'
    return [
        {
            "id": str(allocation["_id"]),  # Convert ObjectId to string
            **allocation,  # Include all other fields
        }
        for allocation in allocations
    ]

async def find_allocation_by_id(allocation_id, db):
    allocation = await db["allocations"].find_one({"_id": ObjectId(allocation_id)})
    return allocation