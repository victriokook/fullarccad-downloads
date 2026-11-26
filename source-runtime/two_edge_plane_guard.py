import math

def validate_pair(cross_length,plane_distance):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (cross_length,plane_distance)):
        raise ValueError('Inputs must be finite real numbers')
    if cross_length<1e-7 or plane_distance<0 or plane_distance>1e-6:
        raise ValueError('Select nonparallel coplanar straight edges')
