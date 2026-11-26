import math

def number(value,limit):
    if type(value) not in (int,float):raise ValueError('Expected builtin numeric input')
    try:value=float(value)
    except (OverflowError,ValueError):raise ValueError('Numeric conversion overflow') from None
    if not math.isfinite(value) or abs(value)>limit:raise ValueError('Nonfinite or out-of-range value')
    return value

def angle_from_reference(parameter,angle):
    parameter=number(parameter,1e6);angle=number(angle,180)
    return (math.degrees(parameter)+angle+180)%360-180

def validate_incidence(dot):
    return number(dot,1e-7)
