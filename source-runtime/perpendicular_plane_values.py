import math

def number(value):
    if type(value) not in (int,float):raise ValueError('Expected builtin numeric input')
    try:value=float(value)
    except (OverflowError,ValueError):raise ValueError('Numeric conversion overflow') from None
    if not math.isfinite(value) or abs(value)>1e6:raise ValueError('Nonfinite or out-of-range value')
    return value

def plane_options(direction,offset):
    if type(direction) is not str or direction not in ('u','v'):raise ValueError('Expected u or v')
    return direction,number(offset)

def checked_point(point):
    if type(point) not in (tuple,list) or len(point)!=3:raise ValueError('Expected three coordinates')
    return tuple(number(value) for value in point)
