import math


def values(number, origin_x, origin_y, bubble_x, bubble_y):
    # Validate number: must be exact int, not bool, in range 1..999999
    if type(number) is not int or isinstance(number, bool):
        raise ValueError("number must be an exact int")
    if number < 1 or number > 999999:
        raise ValueError("number must be in range 1..999999")

    # Validate coordinates: must be int or float, finite, within [-1000000, 1000000]
    coords = [origin_x, origin_y, bubble_x, bubble_y]
    for coord in coords:
        if type(coord) not in (int, float):
            raise ValueError("coordinates must be int or float")
        if isinstance(coord, bool):
            raise ValueError("coordinates must be int or float")
        try: coord = float(coord)
        except OverflowError: raise ValueError("coordinate conversion caused OverflowError")
        if not math.isfinite(coord):
            raise ValueError("coordinates must be finite")
        if coord < -1000000 or coord > 1000000:
            raise ValueError("coordinates must be within [-1000000, 1000000]")

    # Convert to float, catching OverflowError
    try:
        ox = float(origin_x)
        oy = float(origin_y)
        bx = float(bubble_x)
        by = float(bubble_y)
    except OverflowError:
        raise ValueError("coordinate conversion caused OverflowError")

    # Check leader endpoint separation
    distance = math.hypot(bx - ox, by - oy)
    if distance < 0.001:
        raise ValueError("leader endpoints must be separated by >= 0.001mm")

    return (str(number), ox, oy, bx, by)
