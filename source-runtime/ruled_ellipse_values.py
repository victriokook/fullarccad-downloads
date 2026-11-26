import math
def checked_ellipse(major,minor,first,last):
    values=[]
    for value in (major,minor,first,last):
        if type(value) not in (int,float):raise ValueError('Ellipse inputs must be builtin numbers')
        try:value=float(value)
        except (OverflowError,ValueError):raise ValueError('Ellipse input overflow') from None
        if not math.isfinite(value):raise ValueError('Ellipse input must be finite')
        values.append(value)
    major,minor,first,last=values;span=last-first
    if not 1e-6<minor<=major<=1e6 or not math.isfinite(span) or not 1e-7<span<=2*math.pi+1e-9:raise ValueError('Ellipse radii or parameter span outside limits')
    return major,minor,first,last
