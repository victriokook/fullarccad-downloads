import math

def extended_station(distance, length, closed):
    if type(distance) not in (int, float):
        raise ValueError("distance must be exact builtin int or float")
    if type(length) not in (int, float):
        raise ValueError("length must be exact builtin int or float")
    if type(closed) is not bool:
        raise ValueError("closed must be exact builtin bool")

    try:
        distance = float(distance)
        length = float(length)
    except (OverflowError, ValueError):
        raise ValueError("numeric inputs overflow or are invalid")

    if math.isinf(distance) or math.isnan(distance):
        raise ValueError("distance must be finite")
    if math.isinf(length) or math.isnan(length):
        raise ValueError("length must be finite")

    if not (0 <= distance <= 1000000):
        raise ValueError("distance out of range [0, 1000000]")

    if length <= 1e-7 or length > 10000000:
        raise ValueError("length must be strictly greater than 1e-7 and at most 10000000")

    if 0.0 <= distance <= length:
        return (distance, 0.0)
    else:
        if closed:
            raise ValueError("beyond-end distance not allowed in closed mode")
        return (length, distance - length)
