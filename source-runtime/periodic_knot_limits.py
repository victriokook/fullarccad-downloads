"""Finite native periodic curve limits for one new knot."""
import math


def validate_periodic_knot(degree, poles, first, last):
    if type(degree) is not int or type(poles) is not int or not 1 <= degree <= 8 or not degree < poles <= 199:
        raise ValueError('Use degree1..8 and degree<poles<=199')
    if type(first) not in (int, float) or type(last) not in (int, float):
        raise ValueError('Parameter bounds must be exact numeric')
    try:
        if not math.isfinite(first) or not math.isfinite(last):
            raise ValueError('Parameter bounds must be finite')
        period=last-first
        if not math.isfinite(period) or period <= 1e-9:
            raise ValueError('Period must be finite and greater than1e-9')
    except OverflowError as error:
        raise ValueError('Parameter overflow') from error
    return None
