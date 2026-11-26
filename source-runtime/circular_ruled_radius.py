import math

def checked_radius(radius, delta):
    # Convert inputs to float explicitly as per requirement
    if type(radius) not in (int,float) or type(delta) not in (int,float):raise ValueError('Exact numeric values required.')
    try:r,d=float(radius),float(delta)
    except OverflowError:raise ValueError('Numeric overflow.')
    
    # Check for NaN and Infinity in inputs
    if math.isnan(r) or math.isinf(r) or math.isnan(d) or math.isinf(d):
        raise ValueError("Inputs must be finite numbers.")
    
    # Check for bool types (since bool is a subclass of int in Python)
    if isinstance(radius, bool) or isinstance(delta, bool):
        raise ValueError("Boolean inputs are not allowed.")
    
    # Validate source radius range
    if r <= 1e-6 or r > 1000000:
        raise ValueError(f"Source radius must be >1e-6 and <=1000000, got {r}.")
    
    # Calculate target radius
    result = r + d
    
    # Check for negative zero (though float usually handles this, explicit check for safety)
    if result == 0.0:
        raise ValueError("Resulting radius cannot be zero or negative.")
    
    # Validate target radius range
    if result <= 1e-6 or result > 1000000:
        raise ValueError(f"Target radius must be >1e-6 and <=1000000, got {result}.")
    
    return result
