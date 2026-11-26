import math
def check_apex(distance):
    if isinstance(distance, bool):
        raise ValueError("distance must be int or float")
    if type(distance) not in (int,float):
        raise ValueError("distance must be int or float")
    try:
        distance = float(distance)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("distance must be convertible to float")
    
    if distance != distance:
        raise ValueError("distance must be finite")
    
    if not math.isfinite(distance):
        raise ValueError("distance overflow detected")
    
    if distance <= 0.000001:
        raise ValueError("distance must be greater than 0.000001 mm")
    
    return float(distance)
