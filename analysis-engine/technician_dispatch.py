import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import Station, SensorHealthScore, AnomalyFlag
from predictive_degradation import compute_predictive_degradation

def generate_technician_work_orders(db=None):
    """
    Scans AWS stations for degraded or failing sensors and generates structured
    JSON / SMS / WhatsApp field dispatch maintenance work orders.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        stations = db.query(Station).all()
        work_orders = []
        
        for idx, st in enumerate(stations):
            pred = compute_predictive_degradation(st.station_id, db=db)
            rul_days = pred["overall_rul_days"]
            risk = pred["overall_degradation_risk"]
            
            # Generate work order if RUL < 14 days or degradation risk is ELEVATED / CRITICAL
            if rul_days < 14 or risk in ["ELEVATED", "CRITICAL"]:
                # Determine primary degraded variable
                vars_dict = pred["variables"]
                degraded_var = min(
                    [v for v in ["temperature", "humidity", "pressure"] if v in vars_dict],
                    key=lambda v: vars_dict[v]["rul_days"],
                    default="temperature"
                )
                
                var_info = vars_dict.get(degraded_var, {})
                
                # Spare component mapping per variable
                spares_map = {
                    "temperature": ["Pt100 RTD Sensor Element (100 Ohm Class A)", "Thermal Radiation Shield Gasket", "4-20mA Transmitter Modbus Cable"],
                    "humidity": ["Capacitive Polymer Humidity Element", "Sintered Stainless Steel Filter Cap", "Desiccant Calibration Pack"],
                    "pressure": ["Piezoresistive Barometer Transducer Module", "Venting Hose Membrane", "Zero-Point Calibration Kit"]
                }
                
                urgency = "HIGH (48 Hours)" if risk == "CRITICAL" else "MEDIUM (7 Days)"
                
                wo = {
                    "work_order_id": f"WO-2026-AWS-{st.station_id[-3:]}-{idx+101}",
                    "station_id": st.station_id,
                    "station_name": st.name,
                    "coordinates": {"lat": st.lat, "lon": st.lon, "elevation_m": st.elevation_m},
                    "target_variable": degraded_var,
                    "health_score": var_info.get("current_health_score", 65.0),
                    "rul_remaining_days": var_info.get("rul_days", 5),
                    "urgency": urgency,
                    "recommended_spares": spares_map.get(degraded_var, spares_map["temperature"]),
                    "required_tools": ["Digital Multimeter (Fluke 87V)", "Variable Calibrator", "Hex Key Set", "IP67 Enclosure Sealant"],
                    "field_notes": f"Automated AETHERIX Sentinel Dispatch: {st.name} {degraded_var.capitalize()} sensor shows RUL of {var_info.get('rul_days', 5)} days. {var_info.get('proactive_advisory', '')}",
                    "dispatch_json_payload": {
                        "event": "TECHNICIAN_DISPATCH_REQUIRED",
                        "station_id": st.station_id,
                        "lat": st.lat,
                        "lon": st.lon,
                        "fault_variable": degraded_var,
                        "urgency": urgency,
                        "generated_at": datetime.now().isoformat()
                    }
                }
                work_orders.append(wo)
                
        return work_orders
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    orders = generate_technician_work_orders()
    print(f"Generated {len(orders)} Field Technician Work Orders:")
    for o in orders[:2]:
        print(f"  - {o['work_order_id']} | Station: {o['station_name']} | Urgency: {o['urgency']} | Target: {o['target_variable']}")
