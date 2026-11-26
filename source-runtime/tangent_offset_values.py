"""Distance along the displayed tangent-plane normal, including Reverse."""
import math

def checked_distance(value):
    if type(value) not in (int,float):
        raise ValueError('Tangent offset requires a built-in number')
    try:
        result=float(value)
    except OverflowError:
        raise ValueError('Tangent offset must be finite') from None
    if not math.isfinite(result) or not -1e6<=result<=1e6:
        raise ValueError('Tangent offset must be within +/-1000000mm')
    return result

def resolve_distance(value,previous=0.):
    return checked_distance(previous if value is None else value)
