"""Reviewed local-Qwen pivot and three-angle validation,in mm/degrees."""
import math
def checked_ball(origin,yaw,pitch,roll):
    if type(origin) not in (tuple,list) or len(origin)!=3:raise ValueError('Specify three pivot coordinates')
    def number(value,upper):
        if type(value) not in (int,float):raise ValueError('Ball joint inputs require numbers')
        try:value=float(value)
        except OverflowError:raise ValueError('Ball joint input overflow') from None
        if not math.isfinite(value) or abs(value)>upper:raise ValueError('Ball joint input outside its range')
        return value
    return (tuple(number(v,1e6) for v in origin),*(number(v,360) for v in (yaw,pitch,roll)))

