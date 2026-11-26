import math

def validate(count, angle, axis, reverse):
    if type(count) is not int or count < 5 or count > 50:
        raise ValueError("count must be an integer between 5 and 50 inclusive")
    
    if type(angle) not in (int, float):
        raise ValueError("angle must be a number")
    
    try:
        angle_float = float(angle)
    except (OverflowError, ValueError):
        raise ValueError("angle conversion failed")
    
    if math.isfinite(angle_float) is False or angle_float < 0.001 or angle_float > 90:
        raise ValueError("angle must be between 0.001 and 90 degrees inclusive")
    
    if type(axis) is not str:
        raise ValueError("axis must be a string")
    
    if axis not in ('X', 'Y', 'Z'):
        raise ValueError("axis must be one of 'X', 'Y', 'Z'")
    
    if type(reverse) is not bool:
        raise ValueError("reverse must be a boolean")
    
    return count, angle_float, axis, reverse
