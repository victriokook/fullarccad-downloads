import math

def validate_second(height, angle):
    if type(height) not in (int,float):
        raise ValueError("Height must be int or float, not bool")
    if type(angle) not in (int,float):
        raise ValueError("Angle must be int or float, not bool")
    
    try:
        h = float(height)
        a = float(angle)
    except (OverflowError, TypeError, ValueError):
        raise ValueError("Invalid conversion for height or angle")
    
    if not math.isfinite(h) or not math.isfinite(a):
        raise ValueError("Height and angle must be finite numbers")
    
    if h < 0 or h > 100000 or 0<h<.001:
        raise ValueError("Use height0 or .001..100000")
    
    if a < -45 or a > 45:
        raise ValueError("Angle must be between -45 and 45 inclusive")
    
    if h == 0 and a != 0:
        raise ValueError("If height is 0, angle must be 0")
    
    return h, a
