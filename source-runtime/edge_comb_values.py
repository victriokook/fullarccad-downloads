"""Finite display settings for transient native edge curvature sampling."""
import math
def validate(count,scale,flip):
    if type(count) is not int or not 5<=count<=200:raise ValueError('Use5–200 samples.')
    if type(scale) not in (int,float):raise ValueError('Scale must be numeric.')
    try:scale=float(scale)
    except OverflowError:raise ValueError('Scale overflow.')
    if not math.isfinite(scale) or not .001<=scale<=100000:raise ValueError('Scale must be finite,.001–100000mm².')
    if type(flip) is not bool:raise ValueError('Flip must be boolean.')
    return count,scale,flip
