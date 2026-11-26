import math
def checked(tolerance,reduction):
    if any(type(v) not in (int,float) for v in (tolerance,reduction)):raise ValueError('Expected numbers')
    try:t,r=float(tolerance),float(reduction)
    except OverflowError:raise ValueError('Overflow')
    if not (math.isfinite(t) and math.isfinite(r) and 1e-6<=t<=1000 and .001<=r<=.95):raise ValueError('Out of range')
    return t,r
