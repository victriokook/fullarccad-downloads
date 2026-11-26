import math
def validate(count, limit):
    if type(count) is not int:
        raise ValueError("count must be an exact built-in int")
    
    if count < 5 or count > 50:
        raise ValueError("count must be in inclusive range 5..50")
    
    if type(limit) not in (int, float):
        raise ValueError("limit must be an exact built-in int or float")
    
    try:
        limit_float = float(limit)
    except (OverflowError, ValueError):
        raise ValueError("limit conversion failed due to OverflowError or ValueError")
    
    if not math.isfinite(limit_float):
        raise ValueError("limit must be finite")
    
    if limit_float < 1e-12 or limit_float > 1e6:
        raise ValueError("limit must be in inclusive range 1e-12..1e6")
    
    return (count, limit_float)
