import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

client = TestClient(app)

print("=" * 70)
print("TESTING TIER 2 PREDICTIVE DEGRADATION & ESP32 EDGE ENDPOINTS")
print("=" * 70)

# 1. Predictive Health Endpoint
res1 = client.get("/api/sensor-health/predictive/AWS-001")
print(f"GET /api/sensor-health/predictive/AWS-001 -> Status: {res1.status_code}")
if res1.status_code == 200:
    data1 = res1.json()
    print("  Station ID:", data1["station_id"])
    print("  Overall RUL Days:", data1["overall_rul_days"])
    print("  Overall Degradation Risk:", data1["overall_degradation_risk"])
    print("  Temperature RUL & Forecast:", data1["variables"]["temperature"])

# 2. Edge Node Status Endpoint
res2 = client.get("/api/edge/status/AWS-001")
print(f"\nGET /api/edge/status/AWS-001 -> Status: {res2.status_code}")
if res2.status_code == 200:
    data2 = res2.json()
    print("  Firmware Version:", data2["firmware_version"])
    print("  Architecture:", data2["architecture"])
    print("  Edge Latency (ms):", data2["edge_inference_latency_ms"])
    print("  RAM Usage (KB):", data2["ram_usage_kb"])
    print("  Bandwidth Saving (%):", data2["bandwidth_saving_pct"])

print("=" * 70)
