import math

def resolve_fraction(value=None,existing=None):
    if value is None:value=1 if existing is None else existing
    if type(value) not in (int,float):raise ValueError('Expected builtin numeric fraction')
    try:value=float(value)
    except (OverflowError,ValueError):raise ValueError('Numeric conversion overflow') from None
    if not math.isfinite(value) or not .001<=value<=1:raise ValueError('Fraction outside .001..1')
    return value
