import math
def checked_bounds(bounds):
    if type(bounds) not in (list,tuple):
        raise ValueError("Bounds must be a list or tuple")
    if len(bounds) != 4:
        raise ValueError("Bounds must contain exactly four elements")
    
    u1, u2, v1, v2 = bounds
    
    for val in [u1, u2, v1, v2]:
        if isinstance(val, bool):
            raise ValueError("Boolean values are not allowed")
        if type(val) not in (int,float):
            raise ValueError("All bounds must be int or float")
        try:
            val_float = float(val)
        except OverflowError:
            raise ValueError("Bounds cannot be converted to float due to overflow")
        
        if not math.isfinite(val_float):
            raise ValueError("All bounds must be finite numbers")
        if abs(val_float) > 1e6:
            raise ValueError("Absolute value of bounds must be <= 1e6")
    
    u1, u2, v1, v2 = float(u1), float(u2), float(v1), float(v2)
    
    if u2 - u1 <= 1e-9:
        raise ValueError("Difference between u2 and u1 must be greater than 1e-9")
    if v2 - v1 <= 1e-9:
        raise ValueError("Difference between v2 and v1 must be greater than 1e-9")
    
    return (u1, u2, v1, v2)
