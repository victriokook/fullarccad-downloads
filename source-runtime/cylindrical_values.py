"""Reviewed local-Qwen contract for independent cylindrical rotation/travel."""
import math
def checked_motion(origin,axis,angle,distance,limited,minimum,maximum,distance_limited,distance_minimum,distance_maximum):
    def number(value,upper=None):
        if type(value) not in (int,float):raise ValueError('Joint inputs require numbers')
        try:value=float(value)
        except OverflowError:raise ValueError('Joint number overflow') from None
        if not math.isfinite(value) or (upper is not None and abs(value)>upper):raise ValueError('Joint number outside its range')
        return value
    if type(origin) not in (tuple,list) or type(axis) not in (tuple,list) or len(origin)!=3 or len(axis)!=3:raise ValueError('Specify three origin and direction coordinates')
    if type(limited) is not bool or type(distance_limited) is not bool:raise ValueError('Joint limits require boolean switches')
    origin=tuple(number(v,1e6) for v in origin);axis=tuple(number(v) for v in axis);norm=math.hypot(*axis)
    if not math.isfinite(norm) or norm<=1e-9:raise ValueError('Axis must have finite nonzero length')
    axis=tuple(v/norm for v in axis)
    angle,minimum,maximum=(number(v,360) for v in (angle,minimum,maximum));distance,distance_minimum,distance_maximum=(number(v,1e6) for v in (distance,distance_minimum,distance_maximum))
    if limited and (minimum>maximum or not minimum<=angle<=maximum):raise ValueError('Angle must be within its motion limits')
    if distance_limited and (distance_minimum>distance_maximum or not distance_minimum<=distance<=distance_maximum):raise ValueError('Distance must be within its travel limits')
    return dict(kind='cylindrical',origin=origin,axis=axis,angle=angle,distance=distance,limited=limited,minimum=minimum,maximum=maximum,distance_limited=distance_limited,distance_minimum=distance_minimum,distance_maximum=distance_maximum)

