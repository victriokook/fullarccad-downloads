import math

def check_distance(value,tolerance=1e-6):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (value,tolerance)):
        raise ValueError('Invalid distance or tolerance')
    if value<0 or tolerance<=0 or value>tolerance:raise ValueError('Point must lie on the selected bounded face')
    return float(value)
