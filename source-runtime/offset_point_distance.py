import math

def signed_offset(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>1e6:
        raise ValueError('Offset must be finite and within +/-1000000 mm')
    return float(value)
