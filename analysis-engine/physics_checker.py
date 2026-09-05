import math

def check_physics_bounds(variable: str, estimated_value: float, elevation_m: float = 500.0, paired_readings: dict = None) -> tuple[bool, str]:
    """
    Lightweight Physics Sanity Check for weather telemetry estimates:
    - Temperature bounds: [-10.0°C, 55.0°C]
    - Relative Humidity bounds: [0.0%, 100.0%]
    - Pressure bounds: Elevation-adjusted sea level pressure range
    - Dew Point <= Temperature check
    Returns: (passed: bool, details_string: str)
    """
    if estimated_value is None or math.isnan(estimated_value):
        return False, "Estimated value is NaN or None"

    if variable == "temperature":
        if estimated_value < -10.0 or estimated_value > 55.0:
            return False, f"Temperature {estimated_value:.2f}°C violates physical bounds [-10°C, 55°C]"
        if paired_readings and "humidity" in paired_readings:
            rh = paired_readings["humidity"]
            if rh is not None and 0 <= rh <= 100:
                dew_point = estimated_value - ((100.0 - rh) / 5.0)
                if dew_point > estimated_value + 0.1:
                    return False, f"Dew point ({dew_point:.2f}°C) exceeds temperature ({estimated_value:.2f}°C)"
        return True, "Passed temperature physics bounds check"

    elif variable == "humidity":
        if estimated_value < 0.0 or estimated_value > 100.0:
            return False, f"Relative Humidity {estimated_value:.2f}% violates physical bounds [0%, 100%]"
        if paired_readings and "temperature" in paired_readings:
            temp = paired_readings["temperature"]
            if temp is not None:
                dew_point = temp - ((100.0 - estimated_value) / 5.0)
                if dew_point > temp + 0.1:
                    return False, f"Dew point ({dew_point:.2f}°C) exceeds ambient temperature ({temp:.2f}°C)"
        return True, "Passed humidity physics bounds check"

    elif variable == "pressure":
        # Barometric formula for standard atmosphere at elevation
        p_ref = 1013.25 * math.pow(1.0 - 2.25577e-5 * elevation_m, 5.25588)
        p_min = p_ref - 45.0
        p_max = p_ref + 45.0
        if estimated_value < p_min or estimated_value > p_max:
            return False, f"Pressure {estimated_value:.2f} hPa outside realistic elevation-adjusted range [{p_min:.1f}, {p_max:.1f}] hPa for elevation {elevation_m:.0f}m"
        return True, "Passed barometric pressure physics bounds check"

    return True, "Passed general physics check"
