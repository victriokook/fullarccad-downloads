import math

def checked(origin, normal, size):
    """
    Validate and normalize inputs for square geometry.
    
    Returns:
        (origin_tuple, unit_normal_tuple, float_size)
        
    Raises:
        ValueError: If inputs are invalid.
    """
    if type(origin) not in (tuple, list) or len(origin) != 3:
        raise ValueError('origin must be a tuple or list of length 3')
    origin_components = []
    for val in origin:
        if isinstance(val, bool):
            raise ValueError('origin components must be int or float, not bool')
        if type(val) not in (int, float):
            raise ValueError('origin components must be int or float')
        try:
            f_val = float(val)
        except OverflowError:
            raise ValueError('origin component overflow')
        if not math.isfinite(f_val):
            raise ValueError('origin component must be finite')
        if abs(f_val) > 1000000.0:
            raise ValueError('origin component magnitude exceeds 1e6')
        origin_components.append(f_val)
    origin_tuple = tuple(origin_components)
    if type(normal) not in (tuple, list) or len(normal) != 3:
        raise ValueError('normal must be a tuple or list of length 3')
    normal_components = []
    for val in normal:
        if isinstance(val, bool):
            raise ValueError('normal components must be int or float, not bool')
        if type(val) not in (int, float):
            raise ValueError('normal components must be int or float')
        try:
            f_val = float(val)
        except OverflowError:
            raise ValueError('normal component overflow')
        if not math.isfinite(f_val):
            raise ValueError('normal component must be finite')
        if abs(f_val) > 1000000.0:
            raise ValueError('normal component magnitude exceeds 1e6')
        normal_components.append(f_val)
    normal_tuple = tuple(normal_components)
    norm_mag = math.hypot(*normal_tuple)
    if norm_mag <= 1e-12:
        raise ValueError('normal vector magnitude must be > 1e-12')
    inv_norm = 1.0 / norm_mag
    unit_normal_tuple = tuple((n * inv_norm for n in normal_tuple))
    if isinstance(size, bool):
        raise ValueError('size must be int or float, not bool')
    if type(size) not in (int, float):
        raise ValueError('size must be int or float')
    try:
        f_size = float(size)
    except OverflowError:
        raise ValueError('size overflow')
    if not math.isfinite(f_size):
        raise ValueError('size must be finite')
    if f_size < 0.001 or f_size > 100000:
        raise ValueError('size must be between 0.001 and 100000')
    return (origin_tuple, unit_normal_tuple, f_size)

def corners(origin, normal, size):
    """
    Compute the five corners of a centered square in 3D space.
    
    The square is centered at 'origin', lies in the plane defined by 'normal',
    and has side length 'size'. The last corner equals the first to close the loop.
    
    Deterministic in-plane frame selection:
    - Choose the world axis (X, Y, or Z) with the least absolute component in the normal vector.
    - Project this axis onto the plane to get the first basis vector 'u'.
    - Compute 'v' as the cross product of 'normal' and 'u'.
    - This ensures a deterministic frame without relying on arbitrary CAD conventions.
    
    Note: This function computes a finite square display. It does not represent an infinite plane.
    The orientation is determined by the normal vector, but the in-plane rotation is fixed
    by the deterministic axis selection method described above, with no claim of equality to Autodesk's in-plane frame.
    
    Args:
        origin: Tuple or list of 3 numbers (int/float) representing the center.
        normal: Tuple or list of 3 numbers (int/float) representing the plane normal.
        size: Number (int/float) representing the side length of the square.
        
    Returns:
        Tuple of five (x, y, z) tuples representing the corners.
        
    Raises:
        ValueError: If inputs are invalid or resulting coordinates are non-finite or out of bounds.
    """
    origin_tuple, unit_normal_tuple, f_size = checked(origin, normal, size)
    nx, ny, nz = unit_normal_tuple
    abs_nx = abs(nx)
    abs_ny = abs(ny)
    abs_nz = abs(nz)
    min_abs = abs_nx
    axis_idx = 0
    if abs_ny < min_abs:
        min_abs = abs_ny
        axis_idx = 1
    if abs_nz < min_abs:
        min_abs = abs_nz
        axis_idx = 2
    if axis_idx == 0:
        world_axis = (1.0, 0.0, 0.0)
    elif axis_idx == 1:
        world_axis = (0.0, 1.0, 0.0)
    else:
        world_axis = (0.0, 0.0, 1.0)
    dot = world_axis[0] * nx + world_axis[1] * ny + world_axis[2] * nz
    u = (world_axis[0] - dot * nx, world_axis[1] - dot * ny, world_axis[2] - dot * nz)
    u_mag = math.hypot(*u)
    if u_mag < 1e-12:
        raise ValueError('Failed to determine in-plane basis vector u')
    inv_u_mag = 1.0 / u_mag
    u = (u[0] * inv_u_mag, u[1] * inv_u_mag, u[2] * inv_u_mag)
    v = (ny * u[2] - nz * u[1], nz * u[0] - nx * u[2], nx * u[1] - ny * u[0])
    h = f_size / 2.0
    c0 = (origin_tuple[0] - u[0] * h - v[0] * h, origin_tuple[1] - u[1] * h - v[1] * h, origin_tuple[2] - u[2] * h - v[2] * h)
    c1 = (origin_tuple[0] + u[0] * h - v[0] * h, origin_tuple[1] + u[1] * h - v[1] * h, origin_tuple[2] + u[2] * h - v[2] * h)
    c2 = (origin_tuple[0] + u[0] * h + v[0] * h, origin_tuple[1] + u[1] * h + v[1] * h, origin_tuple[2] + u[2] * h + v[2] * h)
    c3 = (origin_tuple[0] - u[0] * h + v[0] * h, origin_tuple[1] - u[1] * h + v[1] * h, origin_tuple[2] - u[2] * h + v[2] * h)
    c4 = c0
    for corner in (c0, c1, c2, c3, c4):
        for coord in corner:
            if not math.isfinite(coord):
                raise ValueError('Corner coordinate is non-finite')
            if abs(coord) > 1000000.0:
                raise ValueError('Corner coordinate magnitude exceeds 1e6')
    return (c0, c1, c2, c3, c4)
