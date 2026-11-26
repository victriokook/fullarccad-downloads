def checked_coordinates(values):
    if type(values) not in (tuple,list):
        raise ValueError("Input must be a tuple or list")
    if len(values) != 3:
        raise ValueError("Input must have exactly 3 elements")
    
    for i, val in enumerate(values):
        # Reject booleans explicitly as they are subclasses of int in Python
        if isinstance(val, bool):
            raise ValueError(f"Element {i} is a boolean, not an int or float")
        
        # Check type: must be int or float (excluding complex)
        if type(val) not in (int,float):
            raise ValueError(f"Element {i} is not an int or float")
        
        # Reject infinity and NaN
        import math
        try:finite=math.isfinite(val)
        except OverflowError as error:raise ValueError("Coordinate overflow") from error
        if not finite:
            raise ValueError(f"Element {i} is not finite")
        
        # Check absolute value bounds
        if abs(val) > 1000000:
            raise ValueError(f"Element {i} exceeds maximum absolute value of 1,000,000")
    
    return tuple(values)
