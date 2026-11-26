import math
def perpendicular_normal(tangent,normal,flip=False):
    if type(flip) is not bool:raise ValueError('Expected boolean flip')
    def unit(vector):
        if type(vector) not in (tuple,list) or len(vector)!=3:raise ValueError('Expected three components')
        if any(type(v) not in (int,float) for v in vector):raise ValueError('Expected exact numeric components')
        try:values=tuple(float(v) for v in vector)
        except (ValueError,OverflowError):raise ValueError('Vector conversion failed') from None
        norm=math.hypot(*values)
        if not all(math.isfinite(v) for v in values) or not math.isfinite(norm) or norm<=1e-9:raise ValueError('Invalid vector magnitude')
        return tuple(v/norm for v in values)
    t=unit(tangent);n=unit(normal)
    cross=unit((t[1]*n[2]-t[2]*n[1],t[2]*n[0]-t[0]*n[2],t[0]*n[1]-t[1]*n[0]))
    return tuple(-v for v in cross) if flip else cross
