"""Reviewed local-Qwen numeric contract for contour flanges."""
import math
def values(thickness,length,radius,side,midplane,reverse):
    if type(side) is not str or side not in ('Inside','Outside','Middle'):raise ValueError('Invalid sheet side')
    if type(midplane) is not bool or type(reverse) is not bool:raise ValueError('Sheet switches must be boolean')
    result=[]
    for value,upper in zip((thickness,length,radius),(1000,100000,100000)):
        if type(value) not in (int,float):raise ValueError('Sheet dimensions require numbers')
        try:value=float(value)
        except OverflowError:raise ValueError('Sheet dimension overflow') from None
        if not math.isfinite(value) or not .001<=value<=upper:raise ValueError('Sheet dimension outside its range')
        result.append(value)
    return (*result,side,midplane,reverse)
