import math

def wall_value(diameter,wall):
    if type(diameter) not in (int,float) or type(wall) not in (int,float):
        raise ValueError('Use built-in numeric values')
    try:d,w=float(diameter),float(wall)
    except (OverflowError,ValueError):raise ValueError('Use finite values') from None
    if not math.isfinite(d) or not math.isfinite(w) or not .001<=d<=100000:
        raise ValueError('Diameter must be finite and .001..100000')
    if w==0:return 0.0
    if not .001<=w<=100000 or w>=d/2:
        raise ValueError('Wall must be zero or .001 <= wall < diameter/2')
    return w
