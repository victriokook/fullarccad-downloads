import math
def checked_direction_shift(distance,angle,direction,normal,reverse=False):
    def number(value):
        if type(value) not in (int,float):raise ValueError('Use exact numeric values')
        try:result=float(value)
        except OverflowError:raise ValueError('Numeric overflow') from None
        if not math.isfinite(result):raise ValueError('Use finite values')
        return result
    distance=number(distance);angle=number(angle)
    if not .001<=distance<=100000 or angle!=0:raise ValueError('Use distance.001..100000 and angle0')
    if type(reverse) is not bool:raise ValueError('Reverse must be bool')
    def unit(value):
        if type(value) not in (tuple,list) or len(value)!=3:raise ValueError('Use3 coordinates')
        vector=tuple(number(v) for v in value);length=math.hypot(*vector)
        if not math.isfinite(length) or length<=1e-9:raise ValueError('Use a finite nonzero direction')
        return tuple(v/length for v in vector)
    direction=unit(direction);normal=unit(normal)
    if abs(sum(a*b for a,b in zip(direction,normal)))<1e-7:raise ValueError('Direction must leave the adjacent plane')
    return tuple(v*distance*(-1 if reverse else 1) for v in direction)
