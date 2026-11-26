import math

def value(low, high, mode='gaussian'):
    if type(mode) is not str:
        raise ValueError("mode must be a string")
    
    valid_modes = {'gaussian', 'principal_min', 'principal_max'}
    if mode not in valid_modes:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes are: {valid_modes}")
    
    if type(low) not in (int, float) or type(high) not in (int, float):
        raise ValueError("low and high must be int or float, not bool")
    
    try:
        low_float = float(low)
        high_float = float(high)
    except (OverflowError, ValueError):
        raise ValueError("low or high cannot be converted to a finite float")
    
    if math.isnan(low_float) or math.isinf(low_float):
        raise ValueError("low must be finite")
    if math.isnan(high_float) or math.isinf(high_float):
        raise ValueError("high must be finite")
    
    if low_float > high_float:
        raise ValueError("low must be less than or equal to high")
    
    if mode == 'gaussian':
        result = low_float * high_float
        if math.isnan(result) or math.isinf(result):
            raise ValueError("Result of gaussian multiplication is not finite")
        return result
    elif mode == 'principal_min':
        return low_float
    elif mode == 'principal_max':
        return high_float
