import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

client = TestClient(app)

print("=" * 70)
print("TESTING ACCURATE IRREGULAR SENSOR STATIONS API STATUS")
print("=" * 70)

res = client.get("/api/stations")
print(f"GET /api/stations -> Status: {res.status_code}")
if res.status_code == 200:
    stations = res.json()
    print(f"Total Stations: {len(stations)}")
    anom_count = sum(1 for s in stations if s["status"] == "ANOMALY")
    norm_count = sum(1 for s in stations if s["status"] == "NORMAL")
    print(f"  Anomalous / Irregular Stations: {anom_count}")
    print(f"  Normal Stations               : {norm_count}\n")
    
    for s in stations:
        print(f"  - [{s['status']:7s}] {s['station_id']} | {s['name']:25s} | Health: {s['health_score']:5.1f} ({s['status_tier']})")

print("=" * 70)
