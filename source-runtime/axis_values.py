import math

def axis_values(origin,direction):
    try:
        raw=tuple(origin)+tuple(direction)
        if len(origin)!=3 or len(direction)!=3 or any(isinstance(v,bool) for v in raw):raise ValueError('Invalid axis values')
        a=tuple(float(v) for v in origin);b=tuple(float(v) for v in direction)
        if not all(math.isfinite(v) for v in a+b):raise ValueError('Nonfinite axis values')
        norm=math.hypot(*b)
        if not math.isfinite(norm) or norm<1e-9:raise ValueError('Direction too short')
        return a,tuple(v/norm for v in b)
    except (TypeError,OverflowError) as error:raise ValueError('Invalid axis values') from error
