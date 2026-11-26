"""Reviewed local-Qwen affine angular ratio,never clamped."""
import math
def linked_angle(driver,driver_zero,follower_zero,one,two,reverse):
    def number(value,lo,hi):
        if type(value) not in (int,float):raise ValueError('Use exact numeric values')
        try:value=float(value)
        except OverflowError:raise ValueError('Motion input overflow') from None
        if not math.isfinite(value) or not lo<=value<=hi:raise ValueError('Motion input outside its range')
        return value
    if type(reverse) is not bool:raise ValueError('Reverse requires bool')
    driver=number(driver,-360,360);driver_zero=number(driver_zero,-360,360);follower_zero=number(follower_zero,-360,360);one=number(one,.001,360);two=number(two,.001,360)
    ratio=two/one
    if not .001<=ratio<=1000:raise ValueError('Ratio must be .001..1000')
    result=follower_zero+(driver-driver_zero)*ratio*(-1 if reverse else 1)
    if not math.isfinite(result) or not -360<=result<=360:raise ValueError('Linked angle exceeds +/-360degrees')
    return result
