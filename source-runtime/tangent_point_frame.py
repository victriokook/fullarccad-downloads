import math
from axis_values import axis_values

def tangent_unit(tangent,normal):
    _,normal=axis_values((0,0,0),normal);_,tangent=axis_values((0,0,0),tangent)
    dot=sum(a*b for a,b in zip(tangent,normal))
    projected=tuple(t-n*dot for t,n in zip(tangent,normal));length=math.hypot(*projected)
    if length<1e-9:raise ValueError('Degenerate surface tangent')
    return tuple(v/length for v in projected)
