"""Input limits for native periodic sketch degree elevation."""
import math


def validate_periodic_curve(degree, poles, period):
    if type(degree) is not int or type(poles) is not int or not 1 <= degree <= 8 or not degree < poles <= 200:
        raise ValueError('Use degree1..8 and degree<poles<=200')
    if type(period) not in (int, float):
        raise ValueError('Period must be exact numeric')
    try:
        if not math.isfinite(period) or period <= 1e-9:
            raise ValueError('Period must be finite and greater than1e-9')
    except OverflowError as error:
        raise ValueError('Period overflow') from error
    return None
