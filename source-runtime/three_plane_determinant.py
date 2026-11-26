import math

def check_determinant(value):
    if type(value) not in (int,float):raise ValueError('Use an exact int or float')
    try:
        if not math.isfinite(value):
            raise ValueError("Input must be finite")
        if abs(value) < 1e-7:
            raise ValueError("Absolute value must be >= 1e-7")
        if abs(value) > 1.000000000001:
            raise ValueError("Value must be <= 1.000000000001")
    except OverflowError:
        raise ValueError("OverflowError caught")
    return value
