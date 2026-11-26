"""Reviewed local-Qwen manual welding text and point validation."""
import math,unicodedata
def validate_text(value):
    if type(value) is not str or len(value)>80 or any(unicodedata.category(c).startswith('C') for c in value):raise ValueError('Use at most80 single-line text characters without controls')
    return value
def validate_point(value):
    if type(value) not in (tuple,list) or len(value)!=2:raise ValueError('Use an XY point')
    result=[]
    for v in value:
        if type(v) not in (int,float):raise ValueError('Coordinates require exact numbers')
        try:v=float(v)
        except OverflowError:raise ValueError('Coordinate overflow') from None
        if not math.isfinite(v) or abs(v)>1e6:raise ValueError('Coordinates exceed +/-1000000mm')
        result.append(v)
    return tuple(result)
