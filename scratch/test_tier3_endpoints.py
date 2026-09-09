import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

client = TestClient(app)

print("=" * 70)
print("TESTING TIER 3 SATELLITE FUSION & TECHNICIAN DISPATCH ENDPOINTS")
print("=" * 70)

# 1. Satellite Verification Endpoint
res1 = client.get("/api/satellite/verify/AWS-001?score=4.5")
print(f"GET /api/satellite/verify/AWS-001?score=4.5 -> Status: {res1.status_code}")
if res1.status_code == 200:
    data1 = res1.json()
    print("  Satellite Source:", data1["satellite_source"])
    print("  Concordance %    :", data1["concordance_pct"])
    print("  Cloud Top Temp(K):", data1["cloud_top_temp_k"])
    print("  Status Label     :", data1["status_label"])

# 2. Technician Dispatch Work Orders Endpoint
res2 = client.get("/api/dispatch/work-orders")
print(f"\nGET /api/dispatch/work-orders -> Status: {res2.status_code}")
if res2.status_code == 200:
    orders = res2.json()
    print(f"  Total Work Orders Generated: {len(orders)}")
    if orders:
        first = orders[0]
        print("  Sample Work Order ID :", first["work_order_id"])
        print("  Station Name         :", first["station_name"])
        print("  Target Variable      :", first["target_variable"])
        print("  Urgency Level        :", first["urgency"])
        print("  Recommended Spares   :", first["recommended_spares"])
        print("  Dispatch JSON Payload:", first["dispatch_json_payload"])

print("=" * 70)
