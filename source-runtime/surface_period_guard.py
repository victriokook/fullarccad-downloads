"""Validate native surface periods without changing parameters."""
import math


def check_period(value):
    if type(value) not in (int, float):
        raise ValueError('Period must be exact numeric')
    try:
        if not math.isfinite(value) or value <= 1e-9:
            raise ValueError('Period must be finite and greater than1e-9')
    except OverflowError as error:
        raise ValueError('Period overflow') from error
    return None
