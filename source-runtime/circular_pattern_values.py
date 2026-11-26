import math
def checked_polar(count,angle,direction,center,reverse=False):
    if type(count) is not int or not 2<=count<=200:raise ValueError('Count must be an integer in2..200')
    if type(reverse) is not bool:raise ValueError('Reverse must be bool')
    def number(value):
        if type(value) not in (int,float):raise ValueError('Use exact numeric values')
        try:result=float(value)
        except OverflowError:raise ValueError('Numeric overflow') from None
        if not math.isfinite(result):raise ValueError('Use finite values')
        return result
    angle=number(angle)
    if not 0<angle<=360:raise ValueError('Angle must be0..360exclusive of0')
    def vector(value):
        if type(value) not in (tuple,list) or len(value)!=3:raise ValueError('Use3 coordinates')
        return tuple(number(v) for v in value)
    direction=vector(direction);center=vector(center);length=math.hypot(*direction)
    if not math.isfinite(length) or length<=1e-9:raise ValueError('Use a finite nonzero direction')
    if any(abs(v)>1e6 for v in center):raise ValueError('Center exceeds +/-1000000mm')
    return count,angle,tuple(v/length*(-1 if reverse else 1) for v in direction),center
