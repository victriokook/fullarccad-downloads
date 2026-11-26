import math
def checked_start(value, current=0.0):
    if type(current) not in (int,float):
        raise ValueError("current must be exact builtin int/float")
    if value is None:value=current
    if type(value) not in (int,float):
        raise ValueError("value must be exact builtin int/float")
    
    try:
        current_f = float(current)
        value_f = float(value)
    except OverflowError:
        raise ValueError("current/value overflow")
    
    if not math.isfinite(current_f) or not (0.0 <= current_f <= 1.0):
        raise ValueError("current must be in [0,1]")
    if not math.isfinite(value_f) or not (0.0 <= value_f <= 1.0):
        raise ValueError("value must be in [0,1]")
    
    if value is None:
        return current_f
    return value_f

def remaining_length(length, start):
    if type(length) not in (int,float):
        raise ValueError("length must be exact builtin int/float")
    
    try:
        length_f = float(length)
    except OverflowError:
        raise ValueError("length overflow")
    
    if not math.isfinite(length_f) or not (1e-7 < length_f <= 1e7):
        raise ValueError("length must be in (1e-7, 1e7]")
    
    start_f = checked_start(start)
    return length_f * (1.0 - start_f)
