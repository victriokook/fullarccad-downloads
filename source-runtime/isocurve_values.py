import math

def validate(axis,fraction):
    if type(axis) is not str or axis not in ('U','V','UV'):raise ValueError('Choose U, V or UV')
    if type(fraction) not in (int,float):raise ValueError('Use a numeric parameter fraction')
    try:value=float(fraction)
    except (OverflowError,TypeError,ValueError):raise ValueError('Invalid parameter fraction') from None
    if not math.isfinite(value) or not .001<=value<=.999:raise ValueError('Use a parameter fraction between .001 and .999')
    return axis,value
