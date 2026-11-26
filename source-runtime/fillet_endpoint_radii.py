def endpoint_radii(first, second):
    if not isinstance(first, (int, float)) or isinstance(first, bool):
        raise ValueError("First radius must be int or float, excluding bool.")
    if not isinstance(second, (int, float)) or isinstance(second, bool):
        raise ValueError("Second radius must be int or float, excluding bool.")
    
    import math
    if first < 0.001 or first > 100000 or second < 0.001 or second > 100000:
        raise ValueError("Radii must be within bounds.")
    if not math.isfinite(first) or not math.isfinite(second):
        raise ValueError("Radii must be finite numbers.")
    
    if first < 0.001 or first > 100000:
        raise ValueError("First radius must be between 0.001 and 100000 inclusive.")
    if second < 0.001 or second > 100000:
        raise ValueError("Second radius must be between 0.001 and 100000 inclusive.")
    
    return float(first), float(second)
