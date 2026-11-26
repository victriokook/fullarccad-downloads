import math

def _number(v):
    if type(v) not in (int,float):raise ValueError('Exact numeric value required')
    try:return float(v)
    except OverflowError:raise ValueError('Numeric overflow')


def validate_grid(lengths, resolution):
    # Validate lengths
    if type(lengths) not in (tuple, list):
        raise ValueError("lengths must be a tuple or list")
    if len(lengths) != 3:
        raise ValueError("lengths must have exactly 3 elements")
    
    lengths=tuple(_number(v) for v in lengths)
    resolution=_number(resolution)
    for l in lengths:
        if isinstance(l, bool):
            raise ValueError("lengths elements must not be bool")
        if not isinstance(l, (int, float)):
            raise ValueError("lengths elements must be int or float")
        if math.isnan(l) or math.isinf(l):
            raise ValueError("lengths elements must be finite")
        if l <= 0:
            raise ValueError("lengths elements must be positive")
        if l > 1000000:
            raise ValueError("lengths elements must be <= 1000000")
    
    # Validate resolution
    if isinstance(resolution, bool):
        raise ValueError("resolution must not be bool")
    if not isinstance(resolution, (int, float)):
        raise ValueError("resolution must be int or float")
    if math.isnan(resolution) or math.isinf(resolution):
        raise ValueError("resolution must be finite")
    if resolution < 0.1 or resolution > 5:
        raise ValueError("resolution must be in range 0.1 to 5")
    
    # Calculate grid dimensions
    grid_dims = []
    for l in lengths:
        dim = math.ceil(l / resolution)
        if dim > 500:
            raise ValueError(f"ceil(length/resolution) exceeds 500 for length {l}")
        grid_dims.append(dim)
    
    # Check product constraint
    product = grid_dims[0] * grid_dims[1] * grid_dims[2]
    if product > 2000000:
        raise ValueError(f"product of grid dimensions {product} exceeds 2000000")
    
    return tuple(grid_dims)
