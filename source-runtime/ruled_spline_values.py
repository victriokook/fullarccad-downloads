import math
def checked_curve(degree,poles,periodic,first,last):
    if type(degree) is not int or type(poles) is not int or not 1<=degree<=9 or not 2<=poles<=50 or degree>=poles:raise ValueError('Curve degree/poles outside limits')
    if type(periodic) is not bool or periodic:raise ValueError('Periodic curves excluded')
    values=[]
    for value in (first,last):
        if type(value) not in (int,float):raise ValueError('Curve parameters must be builtin numbers')
        try:value=float(value)
        except (OverflowError,ValueError):raise ValueError('Curve parameter overflow') from None
        if not math.isfinite(value) or abs(value)>1e6:raise ValueError('Curve parameter outside finite limits')
        values.append(value)
    first,last=values;span=last-first
    if not math.isfinite(span) or span<=1e-9:raise ValueError('Curve parameter span is too small')
    return first,last
