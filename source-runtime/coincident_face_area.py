import math
def contact_area(count,area):
    if type(count) is not int or not 0<=count<=200:raise ValueError('Use0..200 shared faces')
    if type(area) not in (int,float):raise ValueError('Expected builtin numeric area')
    try:value=float(area)
    except (ValueError,OverflowError):raise ValueError('Area conversion failed') from None
    if not math.isfinite(value) or not 0<=value<=1e12:raise ValueError('Area outside finite range')
    return value if count>0 and value>1e-9 else None
