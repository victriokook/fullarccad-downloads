"""Reviewed local-Qwen perpendicular guide vector contract."""
import math
def guide_normal(tangent,delta):
    def vector(values):
        if type(values) not in (tuple,list) or len(values)!=3:raise ValueError('Use three tangent and guide coordinates')
        out=[]
        for value in values:
            if type(value) not in (int,float):raise ValueError('Guide coordinates require numbers')
            try:value=float(value)
            except OverflowError:raise ValueError('Guide coordinate overflow') from None
            if not math.isfinite(value):raise ValueError('Guide coordinates must be finite')
            out.append(value)
        return tuple(out)
    tangent=vector(tangent);delta=vector(delta);length=math.hypot(*tangent)
    if not math.isfinite(length) or length<=1e-9:raise ValueError('Path tangent is degenerate')
    unit=tuple(v/length for v in tangent);dot=sum(a*b for a,b in zip(unit,delta))
    if not math.isfinite(dot):raise ValueError('Guide projection overflow')
    normal=tuple(v-dot*t for v,t in zip(delta,unit));length=math.hypot(*normal)
    if not all(math.isfinite(v) for v in normal) or not math.isfinite(length) or length<=1e-6:raise ValueError('Guide direction is parallel or too close to the path')
    return tuple(v/length for v in normal)
