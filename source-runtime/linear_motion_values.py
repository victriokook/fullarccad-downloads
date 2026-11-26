"""Reviewed local-Qwen angular-to-linear mapping,in degrees and mm."""
import math
def linked_distance(angle,angle_zero,distance_zero,rotation,travel,reverse):
    def number(value,lo,hi):
        if type(value) not in (int,float):raise ValueError('Use exact numeric motion values')
        try:value=float(value)
        except OverflowError:raise ValueError('Motion input overflow') from None
        if not math.isfinite(value) or not lo<=value<=hi:raise ValueError('Motion input outside its range')
        return value
    if type(reverse) is not bool:raise ValueError('Reverse requires bool')
    angle=number(angle,-360,360);angle_zero=number(angle_zero,-360,360);distance_zero=number(distance_zero,-1e6,1e6);rotation=number(rotation,.001,360);travel=number(travel,.001,1e6)
    ratio=travel/rotation
    if not 1e-6<=ratio<=1e6:raise ValueError('Travel per degree must be within1e-6..1e6mm/degree')
    result=distance_zero+(angle-angle_zero)*ratio*(-1 if reverse else 1)
    if not math.isfinite(result) or not -1e6<=result<=1e6:raise ValueError('Linked travel exceeds +/-1000000mm')
    return result
