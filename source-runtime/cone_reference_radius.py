import math

def checked_radius(value):
    if type(value) not in (int,float):
        raise ValueError("Input must be int or float")
    try:
        radius = float(value)
    except OverflowError:
        raise ValueError("Value overflowed during conversion")
    if not math.isfinite(radius):
        raise ValueError("Radius must be finite")
    if not (1e-7 < radius <= 1e6):
        raise ValueError("Radius must be in range (1e-7, 1e6]")
    return radius
