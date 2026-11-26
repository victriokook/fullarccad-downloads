import math
def resolve_backward(value=None,existing=None):
    selected=(existing if existing is not None else 0) if value is None else value
    if type(selected) not in (int,float):raise ValueError('Use an exact builtin numeric fraction')
    try:result=float(selected)
    except (OverflowError,ValueError):raise ValueError('Invalid backward fraction') from None
    if not math.isfinite(result) or (result!=0 and not .001<=result<=1):raise ValueError('Use zero or .001..1')
    return result
