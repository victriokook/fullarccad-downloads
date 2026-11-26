import math

def checked(origin, direction, length):
    """
    Validate and normalize axis parameters.
    
    Args:
        origin: tuple/list of 3 numeric values
        direction: tuple/list of 3 numeric values
        length: numeric value
        
    Returns:
        (origin_tuple, unit_direction_tuple, float_length)
        
    Raises:
        ValueError: if inputs are invalid
    """
    if type(origin) not in (tuple, list) or len(origin) != 3:
        raise ValueError('Origin must be a tuple/list of length 3')
    origin_components = []
    for i, val in enumerate(origin):
        if isinstance(val, bool):
            raise ValueError('Origin components cannot be bool')
        if isinstance(val, str):
            raise ValueError('Origin components cannot be strings')
        if val is None:
            raise ValueError('Origin components cannot be None')
        if type(val) not in (int, float):
            raise ValueError('Origin components must be int or float')
        try:
            fval = float(val)
        except OverflowError:
            raise ValueError('Origin component overflow')
        if not math.isfinite(fval):
            raise ValueError('Origin component must be finite')
        if abs(fval) > 1000000.0:
            raise ValueError('Origin component abs must be <= 1e6')
        origin_components.append(fval)
    origin_tuple = tuple(origin_components)
    if type(direction) not in (tuple, list) or len(direction) != 3:
        raise ValueError('Direction must be a tuple/list of length 3')
    direction_components = []
    for i, val in enumerate(direction):
        if isinstance(val, bool):
            raise ValueError('Direction components cannot be bool')
        if isinstance(val, str):
            raise ValueError('Direction components cannot be strings')
        if val is None:
            raise ValueError('Direction components cannot be None')
        if type(val) not in (int, float):
            raise ValueError('Direction components must be int or float')
        try:
            fval = float(val)
        except OverflowError:
            raise ValueError('Direction component overflow')
        if not math.isfinite(fval):
            raise ValueError('Direction component must be finite')
        if abs(fval) > 1000000.0:
            raise ValueError('Direction component abs must be <= 1e6')
        direction_components.append(fval)
    norm = math.hypot(*direction_components)
    if norm <= 1e-12:
        raise ValueError('Direction norm must be > 1e-12')
    unit_direction = tuple((d / norm for d in direction_components))
    if isinstance(length, bool):
        raise ValueError('Length cannot be bool')
    if isinstance(length, str):
        raise ValueError('Length cannot be string')
    if length is None:
        raise ValueError('Length cannot be None')
    if type(length) not in (int, float):
        raise ValueError('Length must be int or float')
    try:
        float_length = float(length)
    except OverflowError:
        raise ValueError('Length overflow')
    if not math.isfinite(float_length):
        raise ValueError('Length must be finite')
    if float_length < 0.001 or float_length > 100000:
        raise ValueError('Length must be in range 0.001..100000')
    return (origin_tuple, unit_direction, float_length)

def endpoints(origin, direction, length):
    """
    Calculate endpoints of an axis segment.
    
    Args:
        origin: tuple/list of 3 numeric values
        direction: tuple/list of 3 numeric values
        length: numeric value
        
    Returns:
        (start_tuple, end_tuple)
        
    Raises:
        ValueError: if inputs are invalid or endpoints exceed bounds
    """
    origin_tuple, unit_direction, float_length = checked(origin, direction, length)
    half_length = float_length / 2.0
    start = tuple((o - u * half_length for o, u in zip(origin_tuple, unit_direction)))
    end = tuple((o + u * half_length for o, u in zip(origin_tuple, unit_direction)))
    for coord in start:
        if not math.isfinite(coord):
            raise ValueError('Start endpoint coordinate must be finite')
        if abs(coord) > 1000000.0:
            raise ValueError('Start endpoint coordinate abs must be <= 1e6')
    for coord in end:
        if not math.isfinite(coord):
            raise ValueError('End endpoint coordinate must be finite')
        if abs(coord) > 1000000.0:
            raise ValueError('End endpoint coordinate abs must be <= 1e6')
    return (start, end)
