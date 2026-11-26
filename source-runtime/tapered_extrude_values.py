def checked_values(height, angle):
    import math
    
    def convert(val):
        if isinstance(val, bool) or not isinstance(val,(int,float)):
            raise ValueError("Boolean values are not allowed")
        try:
            f = float(val)
        except OverflowError:
            raise ValueError("Value overflowed during conversion")
        return f

    h = convert(height)
    a = convert(angle)
    
    if not math.isfinite(h):
        raise ValueError("Height must be finite")
    if not math.isfinite(a):
        raise ValueError("Angle must be finite")
        
    if not (0.001 <= h <= 100000):
        raise ValueError("Height must be between 0.001 and 100000 inclusive")
    
    if not (-45 <= a <= 45):
        raise ValueError("Angle must be between -45 and 45 inclusive")
        
    return h, a
