import math

def inner_side(kind,size,wall):
    if type(kind) is not str or kind not in ('square','triangle'):
        raise ValueError('Use square or triangle')
    if type(size) not in (int,float) or type(wall) not in (int,float):
        raise ValueError('Use built-in numeric dimensions')
    try:s,w=float(size),float(wall)
    except (OverflowError,ValueError):raise ValueError('Use finite dimensions') from None
    if not math.isfinite(s) or not math.isfinite(w) or not .001<=s<=100000:
        raise ValueError('Size must be finite and .001..100000')
    if w==0:return 0.0
    if not .001<=w<=100000:raise ValueError('Wall must be zero or at least .001')
    inner=s-(2 if kind=='square' else 2*math.sqrt(3))*w
    if inner<=1e-6:raise ValueError('The inner section collapses')
    return inner
