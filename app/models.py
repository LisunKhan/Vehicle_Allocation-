from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from datetime import date, datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)


# Pydantic model for MongoDB documents
class VehicleAllocation(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    employee_id: str
    vehicle_id: str
    driver_id: str
    allocation_date: date
    status: Optional[str] = "active"

    class Config:
        population_by_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

    def to_mongo(self):
        return {
            "employee_id": self.employee_id,
            "vehicle_id": self.vehicle_id,
            "driver_id": self.driver_id,
            "allocation_date": self.allocation_date.isoformat(),  # Convert date to string
            "status": self.status,
        }

    @classmethod
    def from_mongo(cls, data):
        # Convert data from MongoDB format to the Pydantic model
        data['allocation_date'] = datetime.fromisoformat(data['allocation_date']).date()
        return cls(**data)
