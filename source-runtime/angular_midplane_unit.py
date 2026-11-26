import math

def canonical_unit(values):
    if type(values) not in (tuple,list) or len(values) != 3:
        raise ValueError("Input must be a tuple or list of exactly 3 elements.")
    
    for i, v in enumerate(values):
        if isinstance(v, bool):
            raise ValueError(f"Component {i} cannot be a boolean.")
        if type(v) not in (int,float):
            raise ValueError(f"Component {i} must be an int or float.")
        try:finite=math.isfinite(v)
        except OverflowError as error:raise ValueError("Component overflow") from error
        if not finite:
            raise ValueError(f"Component {i} must be finite.")
    
    try:
        norm = math.hypot(*values)
    except OverflowError:
        raise ValueError("Norm overflow occurred.")
    
    if not math.isfinite(norm):
        raise ValueError("Non-finite norm detected.")
    
    if norm <= 1e-10:
        raise ValueError("Norm is too small (<= 1e-10).")
    
    try:
        normalized = tuple(v / norm for v in values)
    except OverflowError:
        raise ValueError("Normalization overflow occurred.")
    
    max_idx = 0
    max_abs = abs(normalized[0])
    
    for i in range(1, 3):
        if abs(normalized[i]) > max_abs:
            max_abs = abs(normalized[i])
            max_idx = i
    
    if normalized[max_idx] < 0:
        return tuple(-v for v in normalized)
    
    return normalized
