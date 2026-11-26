import math
def checked(cx,cy,major,minor,rotation,start,sweep):
    raw=(cx,cy,major,minor,rotation,start,sweep)
    if any(type(v) not in (int,float) for v in raw):raise ValueError('Expected numbers')
    try:values=tuple(float(v) for v in raw)
    except OverflowError:raise ValueError('Overflow')
    if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite')
    x,y,a,b,r,t,s=values
    if not (.001<=b<a<=100000 and a-b>1e-6 and abs(x)+a<=1e6 and abs(y)+a<=1e6 and abs(r)<=360 and abs(t)<=360 and .001<=s<=359.999):raise ValueError('Out of range')
    return x,y,a,b,r%360,t%360,s
