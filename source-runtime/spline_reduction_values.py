import math

def validate_tolerance(value):
    if type(value) not in (int, float):
        raise ValueError("Use an exact int or float, not bool or text")
    
    try:
        numeric_value = float(value)
    except (OverflowError, TypeError, ValueError):
        raise ValueError("Invalid conversion to float")
    
    if not math.isfinite(numeric_value):
        raise ValueError("Value must be finite")
    
    if numeric_value < 0.000001 or numeric_value > 10.0:
        raise ValueError("Value must be between 0.000001 and 10.0 inclusive")
    
    return numeric_value
