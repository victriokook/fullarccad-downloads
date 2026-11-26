import math

def vertices(center, sides, apothem, angle):
    if type(center) not in (tuple, list) or len(center) != 2:
        raise ValueError('Expected two coordinates')
    if type(sides) is not int:
        raise ValueError('Sides must be exact int')
    if any((type(value) not in (int, float) for value in (*center, apothem, angle))):
        raise ValueError('Expected exact numeric types')
    if isinstance(sides, bool) or not isinstance(sides, int):
        raise ValueError('sides must be an integer')
    if sides < 3 or sides > 50:
        raise ValueError('sides must be between 3 and 50')
    if isinstance(apothem, bool):
        raise ValueError('apothem must be numeric')
    if isinstance(apothem, str):
        raise ValueError('apothem must be numeric')
    if not isinstance(apothem, (int, float)):
        raise ValueError('apothem must be numeric')
    try:
        apothem = float(apothem)
    except (OverflowError, ValueError):
        raise ValueError('apothem conversion failed')
    if not math.isfinite(apothem):
        raise ValueError('apothem must be finite')
    if apothem < 0.001 or apothem > 100000:
        raise ValueError('apothem must be between 0.001 and 100000')
    if isinstance(angle, bool):
        raise ValueError('angle must be numeric')
    if isinstance(angle, str):
        raise ValueError('angle must be numeric')
    if not isinstance(angle, (int, float)):
        raise ValueError('angle must be numeric')
    try:
        angle = float(angle)
    except (OverflowError, ValueError):
        raise ValueError('angle conversion failed')
    if not math.isfinite(angle):
        raise ValueError('angle must be finite')
    if angle < -360 or angle > 360:
        raise ValueError('angle must be between -360 and 360')
    if not isinstance(center, (tuple, list)):
        raise ValueError('center must be a tuple or list')
    if len(center) != 2:
        raise ValueError('center must have length 2')
    cx, cy = center
    if isinstance(cx, bool) or isinstance(cy, bool):
        raise ValueError('center coordinates must be numeric')
    if isinstance(cx, str) or isinstance(cy, str):
        raise ValueError('center coordinates must be numeric')
    if not isinstance(cx, (int, float)) or not isinstance(cy, (int, float)):
        raise ValueError('center coordinates must be numeric')
    try:
        cx = float(cx)
        cy = float(cy)
    except (OverflowError, ValueError):
        raise ValueError('center conversion failed')
    if not math.isfinite(cx) or not math.isfinite(cy):
        raise ValueError('center coordinates must be finite')
    if abs(cx) > 1000000.0 or abs(cy) > 1000000.0:
        raise ValueError('center coordinates must be <= 1e6 in absolute value')
    radius = apothem / math.cos(math.pi / sides)
    first_angle_rad = math.radians(angle) - math.pi / sides
    result = []
    for i in range(sides):
        theta = first_angle_rad + 2 * math.pi * i / sides
        x = cx + radius * math.cos(theta)
        y = cy + radius * math.sin(theta)
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError('output coordinate is not finite')
        if abs(x) > 1000000.0 or abs(y) > 1000000.0:
            raise ValueError('output coordinate exceeds 1e6 in absolute value')
        result.append((x, y, 0.0))
    result.append(result[0])
    return tuple(result)
