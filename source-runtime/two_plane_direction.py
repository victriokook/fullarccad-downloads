import math
from axis_values import axis_values

def cross_direction(a,b):
    _,a=axis_values((0,0,0),a);_,b=axis_values((0,0,0),b)
    c=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    h=math.hypot(*c)
    if h<1e-7:raise ValueError('Planes are parallel or nearly parallel')
    return tuple(v/h for v in c)
