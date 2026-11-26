import math

def checked_direction(values):
    if type(values) not in (tuple,list) or len(values)!=3:raise ValueError('Expected three direction components')
    if any(type(v) not in (int,float) for v in values):raise ValueError('Expected builtin numeric direction components')
    try:components=tuple(float(v) for v in values)
    except (ValueError,TypeError,OverflowError) as error:raise ValueError('Invalid direction components') from error
    if not all(math.isfinite(v) for v in components):raise ValueError('Direction must be finite')
    length=math.hypot(*components)
    if not math.isfinite(length) or length<=1e-9:raise ValueError('Direction has invalid length')
    return tuple(v/length for v in components)
