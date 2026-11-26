import math

def endpoints(center, length, angle):
    if type(center) not in (tuple, list) or len(center) != 2:
        raise ValueError('Expected two center coordinates')

    def number(value):
        if type(value) not in (int, float):
            raise ValueError('Expected exact int or float')
        try:
            out = float(value)
        except OverflowError as error:
            raise ValueError('Numeric overflow') from error
        if not math.isfinite(out):
            raise ValueError('Nonfinite value')
        return out
    center = tuple((number(value) for value in center))
    length = number(length)
    angle = number(angle)
    if not isinstance(center, (tuple, list)):
        raise ValueError('center must be a tuple or list')
    if len(center) != 2:
        raise ValueError('center must have length 2')
    cx, cy = center
    if isinstance(cx, bool) or isinstance(cy, bool):
        raise ValueError('center values must be numeric, not bool')
    if not isinstance(cx, (int, float)) or not isinstance(cy, (int, float)):
        raise ValueError('center values must be int or float')
    if not math.isfinite(cx) or not math.isfinite(cy):
        raise ValueError('center coordinates must be finite')
    if abs(cx) > 1000000 or abs(cy) > 1000000:
        raise ValueError('center coordinates must be <= 1000000 in abs')
    if isinstance(length, bool):
        raise ValueError('length must be numeric, not bool')
    if not isinstance(length, (int, float)):
        raise ValueError('length must be int or float')
    if not math.isfinite(length):
        raise ValueError('length must be finite')
    if length < 0.001 or length > 1000000:
        raise ValueError('length must be between 0.001 and 1000000')
    if isinstance(angle, bool):
        raise ValueError('angle must be numeric, not bool')
    if not isinstance(angle, (int, float)):
        raise ValueError('angle must be int or float')
    if not math.isfinite(angle):
        raise ValueError('angle must be finite')
    if angle < -360 or angle > 360:
        raise ValueError('angle must be between -360 and 360')
    half_length = length / 2.0
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    dx = half_length * cos_a
    dy = half_length * sin_a
    start_x = cx - dx
    start_y = cy - dy
    end_x = cx + dx
    end_y = cy + dy
    if not math.isfinite(start_x) or not math.isfinite(start_y):
        raise ValueError('start coordinates overflow')
    if not math.isfinite(end_x) or not math.isfinite(end_y):
        raise ValueError('end coordinates overflow')
    if abs(start_x) > 1000000 or abs(start_y) > 1000000:
        raise ValueError('start coordinates exceed limit')
    if abs(end_x) > 1000000 or abs(end_y) > 1000000:
        raise ValueError('end coordinates exceed limit')
    return ((start_x, start_y, 0.0), (end_x, end_y, 0.0))
