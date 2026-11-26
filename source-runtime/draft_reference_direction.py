"""Finite bounded native direction normalization."""
import math
def unit_direction(x,y,z):
    if any(type(v) not in (int,float) for v in (x,y,z)):raise ValueError('Use finite numeric components.')
    try:values=tuple(float(v) for v in (x,y,z))
    except (OverflowError,ValueError) as error:raise ValueError('Direction conversion overflows.') from error
    if any(not math.isfinite(v) or abs(v)>1e6 for v in values):raise ValueError('Direction components exceed bounds.')
    norm=math.hypot(*values)
    if not math.isfinite(norm) or norm<1e-9:raise ValueError('Direction has zero or unsupported length.')
    return tuple(v/norm for v in values)
