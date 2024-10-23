import logging

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

from app.config import MONGO_DETAILS
from app.crud import create_allocation, update_allocation, delete_allocation, get_allocation_history, \
    find_allocation_by_id
from app.schemas import AllocationCreate, AllocationUpdate, AllocationOut, AllocationResponse
from typing import Optional

app = FastAPI()

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.vehicle_allocation_db

# Dependency to inject the db into the route
def get_db():
    return db

@app.on_event("startup")
async def connect_db():
    # Startup event to connect to MongoDB
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def disconnect_db():
    # Shutdown event to close MongoDB connection
    client.close()
    print("Disconnected from MongoDB")


# API routes

@app.post("/allocations/", response_model=AllocationOut)
async def allocate_vehicle(allocation: AllocationCreate, db=Depends(get_db)):
    try:
        allocation_id = await create_allocation(allocation, db)
        return {**allocation.dict(), "id": allocation_id}
    except ValueError as e:
        logging.error(f"Error allocating vehicle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.patch("/allocations/{allocation_id}", response_model=AllocationOut)
async def update_allocation(allocation_id: str, update: AllocationUpdate):
    # Fetch existing allocation to check if it exists
    existing_allocation = await db["allocations"].find_one({"_id": ObjectId(allocation_id)})

    if not existing_allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Create a dictionary to hold the updated fields
    update_data = {k: v for k, v in update.dict().items() if v is not None}

    # Debugging: Log the update data
    print(f"Update data for allocation {allocation_id}: {update_data}")

    # Update the allocation in the database
    result = await db["allocations"].update_one({"_id": ObjectId(allocation_id)}, {"$set": update_data})

    # Check if the update was successful
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made or allocation not found")

    # Fetch the updated allocation to return it
    updated_allocation = await db["allocations"].find_one({"_id": ObjectId(allocation_id)})

    if not updated_allocation:
        raise HTTPException(status_code=404, detail="Allocation not found after update")

    # Return the updated allocation including the required fields
    return AllocationOut(
        id=str(updated_allocation["_id"]),
        employee_id=updated_allocation["employee_id"],
        vehicle_id=updated_allocation["vehicle_id"],
        driver_id=updated_allocation["driver_id"],
        allocation_date=updated_allocation["allocation_date"],
        status=updated_allocation["status"],
    )


@app.delete("/allocations/{allocation_id}")
async def delete_allocation(allocation_id: str):
    try:
        # Attempt to delete the allocation
        result = await db.allocations.delete_one({"_id": ObjectId(allocation_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Allocation not found")
        return {"detail": "Allocation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/allocations/history/", response_model=List[AllocationOut])
async def allocation_history(employee_id: Optional[str] = None, vehicle_id: Optional[str] = None, db=Depends(get_db)):
    """
    Fetch allocation history, optionally filtered by employee or vehicle.
    """
    allocations = await get_allocation_history(employee_id, vehicle_id, db)
    return [AllocationOut(**allocation) for allocation in allocations]


@app.get("/allocations/{allocation_id}", response_model=AllocationResponse)
async def read_allocation(allocation_id: str):
    allocation = await db.allocations.find_one({"_id": ObjectId(allocation_id)})
    if allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return AllocationResponse.from_mongo(allocation)