import math

def draft_angle(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<value<=45:
        raise ValueError('Draft angle must be finite and greater than0 through45 degrees')
    return float(value)
