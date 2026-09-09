import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.crud import get_all_stations_with_status, get_recent_alerts, get_station_history, get_sensor_health_details

db = SessionLocal()
stations = get_all_stations_with_status(db)

print("=" * 70)
print("PART 2 — AUDIT OF 3 STATIONS ACROSS HEALTH TIERS")
print("=" * 70)

# Pick 3 stations across health tiers
healthy = next(s for s in stations if s['status_tier'] == 'Healthy')
watch = next(s for s in stations if s['status_tier'] == 'Watch')
degraded_or_critical = next((s for s in stations if s['status_tier'] in ['Degraded', 'Critical']), stations[0])

test_stations = [healthy, watch, degraded_or_critical]

for st in test_stations:
    print(f"\n--- Station: {st['station_id']} ({st['name']}) ---")
    print(f"  Backend Tier     : {st['status_tier']} (Score: {st['health_score']})")
    print(f"  Backend Status   : {st['status']}")
    print(f"  Maintenance Rec  : {st['maintenance_recommendation']}")
    
    # Check recent alert for station
    alerts = get_recent_alerts(db, limit=50)
    st_alerts = [a for a in alerts if a['station_id'] == st['station_id']]
    if st_alerts:
        latest = st_alerts[0]
        print(f"  Latest Alert     : Var={latest['variable']}, Fault={latest['predicted_fault_type']}, Conf={latest['ml_confidence']:.2f}")
        print(f"  XAI Narrative    : {latest['explanation_text']}")
    else:
        print(f"  Latest Alert     : No active alerts in recent 50 flagged items.")

db.close()
