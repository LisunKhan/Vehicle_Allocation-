from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

# Request model for creating an allocation
class AllocationCreate(BaseModel):
    employee_id: str
    vehicle_id: str
    driver_id: str
    allocation_date: date
    status: Optional[str] = "active"

    def to_mongo(self):
        return {
            "employee_id": self.employee_id,
            "vehicle_id": self.vehicle_id,
            "driver_id": self.driver_id,
            "allocation_date": self.allocation_date.isoformat(),  # Convert date to string
            "status": self.status,
        }

# Request model for updating an allocation
class AllocationUpdate(BaseModel):
    allocation_date: Optional[str] = None
    status: Optional[str] = None  # 'active' or 'canceled'
# Response model for an allocation
class AllocationOut(AllocationCreate):
    id: str
    status: str

class AllocationResponse(BaseModel):
    id: str = Field(alias="_id")  # This will accept an ObjectId but serialize as a string
    employee_id: str
    vehicle_id: str
    driver_id: str
    allocation_date: date
    status: Optional[str] = "active"
    # Add other fields from your allocation here

    class Config:
        allow_population_by_field_name = True  # Allows using field names when creating an instance
        arbitrary_types_allowed = True  # Allows using arbitrary types like ObjectId

    @classmethod
    def from_mongo(cls, allocation):
        allocation_dict = allocation.copy()
        allocation_dict['_id'] = str(allocation_dict['_id'])  # Convert ObjectId to string
        return cls(**allocation_dict)