import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 12 Fictional AWS stations in Western Ghats / Maharashtra region
STATIONS = [
    {"station_id": "AWS-001", "name": "Pune Central", "lat": 18.5204, "lon": 73.8567, "elevation_m": 560.0},
    {"station_id": "AWS-002", "name": "Pimpri-Chinchwad", "lat": 18.6298, "lon": 73.7997, "elevation_m": 570.0},
    {"station_id": "AWS-003", "name": "Lonavala Hill Top", "lat": 18.7557, "lon": 73.4091, "elevation_m": 620.0},
    {"station_id": "AWS-004", "name": "Mahabaleshwar Peak", "lat": 17.9237, "lon": 73.6586, "elevation_m": 1353.0},
    {"station_id": "AWS-005", "name": "Satara North", "lat": 17.6805, "lon": 74.0183, "elevation_m": 742.0},
    {"station_id": "AWS-006", "name": "Lavasa Valley", "lat": 18.4104, "lon": 73.5074, "elevation_m": 640.0},
    {"station_id": "AWS-007", "name": "Shirur Agro Station", "lat": 18.8267, "lon": 74.3783, "elevation_m": 565.0},
    {"station_id": "AWS-008", "name": "Baramati Plain", "lat": 18.1517, "lon": 74.5786, "elevation_m": 538.0},
    {"station_id": "AWS-009", "name": "Khandala Pass", "lat": 18.7610, "lon": 73.3725, "elevation_m": 550.0},
    {"station_id": "AWS-010", "name": "Wai River Basin", "lat": 17.9469, "lon": 73.8967, "elevation_m": 718.0},
    {"station_id": "AWS-011", "name": "Bhor Foothills", "lat": 18.1518, "lon": 73.8436, "elevation_m": 585.0},
    {"station_id": "AWS-012", "name": "Rajgurunagar AWS", "lat": 18.8550, "lon": 73.8860, "elevation_m": 650.0},
]


def generate_clean_weather_data(start_date="2026-03-01", days=180, seed=42):
    """
    Generates realistic hourly weather data for 12 AWS stations over a 6-month period.
    Models diurnal cycles, seasonal progression, elevation lapse rate, and regional spatial correlation.
    """
    np.random.seed(seed)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    num_hours = days * 24
    timestamps = [start_dt + timedelta(hours=i) for i in range(num_hours)]
    
    # Pre-generate regional weather driver components (common weather front / cloud cover)
    # Seasonal temperature trend (Summer peak around day 60-70, monsoon dip day 100-180)
    day_numbers = np.array([(ts - start_dt).total_seconds() / 86400.0 for ts in timestamps])
    seasonal_temp_offset = 5.0 * np.sin(2 * np.pi * (day_numbers - 30) / 365.0)
    
    # Regional weather noise (slow moving synoptic scale variations over 2-4 days)
    synoptic_wave = 3.0 * np.sin(2 * np.pi * day_numbers / 3.5) + np.random.normal(0, 0.8, size=num_hours)
    synoptic_humidity_wave = -4.0 * synoptic_wave + np.random.normal(0, 2.0, size=num_hours)
    
    station_dfs = []
    
    for station in STATIONS:
        elev = station["elevation_m"]
        
        # Elevation lapse rate adjustments
        temp_lapse = (elev - 500.0) * (6.5 / 1000.0)  # -0.65°C per 100m above 500m
        base_pressure = 1013.25 * ((1.0 - (0.0065 * elev / 288.15)) ** 5.2558)
        
        temps = []
        humidities = []
        pressures = []
        
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            d_num = day_numbers[i]
            
            # Diurnal Temperature Cycle (Peak ~14:00, Minimum ~05:00)
            diurnal_temp = 7.0 * np.sin(2 * np.pi * (hour - 9) / 24.0)
            
            # Base regional temp ~28°C + seasonal + diurnal - elevation lapse + synoptic + local station noise
            station_noise_t = np.random.normal(0, 0.4)
            temp = 28.0 + seasonal_temp_offset[i] + diurnal_temp - temp_lapse + (0.5 * synoptic_wave[i]) + station_noise_t
            temp = np.clip(temp, 12.0, 44.0)
            
            # Diurnal Humidity Cycle (Inversely correlated with temp)
            diurnal_hum = -20.0 * np.sin(2 * np.pi * (hour - 9) / 24.0)
            monsoon_hum = 15.0 if d_num > 90 else 0.0  # Monsoon boost after June
            station_noise_h = np.random.normal(0, 1.2)
            hum = 55.0 - (1.2 * diurnal_temp) + diurnal_hum + monsoon_hum + (0.4 * synoptic_humidity_wave[i]) + station_noise_h
            hum = np.clip(hum, 18.0, 98.0)
            
            # Pressure (Base elevation pressure + diurnal atmospheric tide + synoptic wave)
            diurnal_pres = 1.2 * np.cos(2 * np.pi * (hour - 10) / 12.0)  # Semi-diurnal 12h tide
            station_noise_p = np.random.normal(0, 0.15)
            pres = base_pressure + diurnal_pres - (0.1 * (temp - 25.0)) + station_noise_p
            
            temps.append(round(float(temp), 2))
            humidities.append(round(float(hum), 2))
            pressures.append(round(float(pres), 2))
            
        df_st = pd.DataFrame({
            "station_id": station["station_id"],
            "timestamp": timestamps,
            "temperature": temps,
            "humidity": humidities,
            "pressure": pressures
        })
        station_dfs.append(df_st)
        
    all_readings = pd.concat(station_dfs, ignore_index=True)
    return all_readings
