from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test the POST /allocations/ route
def test_create_allocation():
    allocation_data = {
        "employee_id": "emp1",
        "vehicle_id": "veh1",
        "driver_id": "drv1",
        "allocation_date": "2024-10-30"
    }
    response = client.post("/allocations/", json=allocation_data)
    assert response.status_code == 200
    assert "id" in response.json()

# Add more tests for update, delete, and history retrieval
