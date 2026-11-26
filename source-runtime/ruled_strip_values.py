import math


def checked_values(distance, angle, mode, reverse):
    # Validate distance type
    if type(distance) not in (int,float):
        raise ValueError("distance must be numeric (int or float)")
    
    # Reject bool for distance
    if isinstance(distance, bool):
        raise ValueError("distance cannot be a boolean")
    
    # Validate angle type
    if type(angle) not in (int,float):
        raise ValueError("angle must be numeric (int or float)")
    
    # Reject bool for angle
    if isinstance(angle, bool):
        raise ValueError("angle cannot be a boolean")
    
    # Check distance range and finiteness
    try:
        dist_float = float(distance)
    except OverflowError:
        raise ValueError("distance is too large (overflow)")
    
    if math.isinf(dist_float) or math.isnan(dist_float):
        raise ValueError("distance must be finite")
    
    if not (0.001 <= dist_float <= 100000):
        raise ValueError("distance must be between 0.001 and 100000 inclusive")
    
    # Check angle range and finiteness
    try:
        ang_float = float(angle)
    except OverflowError:
        raise ValueError("angle is too large (overflow)")
    
    if math.isinf(ang_float) or math.isnan(ang_float):
        raise ValueError("angle must be finite")
    
    if not (-89 <= ang_float <= 89):
        raise ValueError("angle must be between -89 and 89 inclusive")
    
    # Validate mode type (must be exact str)
    if type(mode) is not str:
        raise ValueError("mode must be a string")
    
    if mode != 'normal' and mode != 'tangent':
        raise ValueError("mode must be exactly 'normal' or 'tangent'")
    
    # Validate reverse type (must be exact bool)
    if type(reverse) is not bool:
        raise ValueError("reverse must be a boolean")
    
    return (dist_float, ang_float, mode, reverse)
