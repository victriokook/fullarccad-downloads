import math
from path_pattern_start_values import checked_start

def closed_positions(length, start, count, mode='full', distance=10):
    if type(length) not in (int,float):
        raise ValueError("length must be numeric")
    if type(start) not in (int,float):
        raise ValueError("start must be numeric")
    if type(count) is not int:
        raise ValueError("count must be integer")
    if type(mode) is not str:
        raise ValueError("mode must be string")
    if type(distance) not in (int,float):
        raise ValueError("distance must be numeric")

    try:
        length=float(length);distance=float(distance)
    except OverflowError:
        raise ValueError('Numeric overflow') from None
    if not math.isfinite(length) or not math.isfinite(distance):raise ValueError('Nonfinite input')
    start = checked_start(start)
    if start >= 1:
        raise ValueError("start must be less than 1")

    if length <= 0 or length > 1e7 or length <= 1e-7:
        raise ValueError("length out of range")
    if distance < 0.001 or distance > 1e6:
        raise ValueError("distance out of range")
    if count < 2 or count > 200:
        raise ValueError("count out of range")

    if mode not in ('full', 'spacing', 'extent'):
        raise ValueError("mode must be full, spacing, or extent")

    tolerance = max(1e-7, length * 1e-9)

    if mode == 'full':
        extent = length
    elif mode == 'spacing':
        extent = distance * (count - 1)
    else:  # mode == 'extent'
        extent = distance

    if extent > length + tolerance:
        raise ValueError("extent exceeds length")

    full_loop = abs(extent - length) <= tolerance

    if mode == 'spacing' and full_loop:
        raise ValueError("spacing mode with full loop rejected to avoid duplicates")

    divisor = count if full_loop else count - 1
    step = min(extent, length) / divisor

    if step <= 1e-7:
        raise ValueError("step too small")

    positions = tuple(start * length + i * step for i in range(count))
    return positions, min(extent, length)
