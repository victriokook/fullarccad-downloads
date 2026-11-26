import math

def checked(x, y, z):
    """
    Validate and convert x, y, z to floats.
    Rejects bool, other subclasses, strings, None, and arbitrary float objects.
    Accepts only exact builtin int or float.
    Ensures values are finite and abs <= 1000000.
    """

    def validate_single(val, name):
        if isinstance(val, bool):
            raise ValueError(f'{name} is a bool')
        if val is None:
            raise ValueError(f'{name} is None')
        if isinstance(val, str):
            raise ValueError(f'{name} is a string')
        if type(val) is not int and type(val) is not float:
            raise ValueError(f'{name} is not an exact builtin int or float')
        try:
            f_val = float(val)
        except OverflowError:
            raise ValueError(f'{name} caused overflow during conversion')
        if not math.isfinite(f_val):
            raise ValueError(f'{name} is not finite')
        if abs(f_val) > 1000000:
            raise ValueError(f'abs({name}) > 1000000')
        return f_val
    fx = validate_single(x, 'x')
    fy = validate_single(y, 'y')
    fz = validate_single(z, 'z')
    return (fx, fy, fz)

def preview_points(x, y, z, size=1.0):
    """
    Returns tuple of six coordinate triples describing three independent orthogonal line segments
    centred at (x,y,z), length 2*size each along X, Y, Z axes.
    
    Validates size: must be positive, finite, and <= 1000.
    Calls checked to validate x, y, z.
    """
    if isinstance(size, bool):
        raise ValueError('size is a bool')
    if size is None:
        raise ValueError('size is None')
    if isinstance(size, str):
        raise ValueError('size is a string')
    if type(size) is not int and type(size) is not float:
        raise ValueError('size is not an exact builtin int or float')
    try:
        f_size = float(size)
    except OverflowError:
        raise ValueError('size caused overflow during conversion')
    if not math.isfinite(f_size):
        raise ValueError('size is not finite')
    if f_size <= 0:
        raise ValueError('size must be positive')
    if f_size > 1000:
        raise ValueError('size > 1000')
    cx, cy, cz = checked(x, y, z)
    half_size = f_size
    p1_x = cx - half_size
    p2_x = cx + half_size
    seg1 = ((p1_x, cy, cz), (p2_x, cy, cz))
    p1_y = cy - half_size
    p2_y = cy + half_size
    seg2 = ((cx, p1_y, cz), (cx, p2_y, cz))
    p1_z = cz - half_size
    p2_z = cz + half_size
    seg3 = ((cx, cy, p1_z), (cx, cy, p2_z))
    return seg1 + seg2 + seg3
