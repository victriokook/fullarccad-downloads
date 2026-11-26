def validate_stepover(value, diameter, width, height):
    """
    Validate stepover parameters for offline rectangular CAM pocketing.
    
    Args:
        value: stepover percentage (5..80 inclusive)
        diameter: tool diameter (.01..1000)
        width: pocket width (.01..100000)
        height: pocket height (.01..100000)
    
    Returns:
        stepover percentage as float
    
    Raises:
        ValueError: if any parameter is invalid
    """
    # Reject bools first (bool is subclass of int)
    if isinstance(value, bool) or isinstance(diameter, bool) or isinstance(width, bool) or isinstance(height, bool):
        raise ValueError("Boolean values are not allowed")
    
    # Reject non-int/float types
    if type(value) not in (int, float):
        raise ValueError("value must be int or float")
    if type(diameter) not in (int, float):
        raise ValueError("diameter must be int or float")
    if type(width) not in (int, float):
        raise ValueError("width must be int or float")
    if type(height) not in (int, float):
        raise ValueError("height must be int or float")
    
    # Reject strings explicitly (though isinstance check above should catch them)
    if isinstance(value, str) or isinstance(diameter, str) or isinstance(width, str) or isinstance(height, str):
        raise ValueError("String values are not allowed")
    
    # Convert to float for processing
    try:
        value_f = float(value)
        diameter_f = float(diameter)
        width_f = float(width)
        height_f = float(height)
    except (OverflowError, ValueError):
        raise ValueError("Value conversion failed")
    
    # Check for NaN and infinity
    import math
    if math.isnan(value_f) or math.isinf(value_f):
        raise ValueError("value must be finite")
    if math.isnan(diameter_f) or math.isinf(diameter_f):
        raise ValueError("diameter must be finite")
    if math.isnan(width_f) or math.isinf(width_f):
        raise ValueError("width must be finite")
    if math.isnan(height_f) or math.isinf(height_f):
        raise ValueError("height must be finite")
    
    # Validate stepover percentage range: 5..80 inclusive
    if value_f < 5.0 or value_f > 80.0:
        raise ValueError("stepover percent must be between 5 and 80 inclusive")
    
    # Validate diameter range: .01..1000
    if diameter_f < 0.01 or diameter_f > 1000.0:
        raise ValueError("diameter must be between 0.01 and 1000")
    
    # Validate width range: .01..100000
    if width_f < 0.01 or width_f > 100000.0:
        raise ValueError("width must be between 0.01 and 100000")
    
    # Validate height range: .01..100000
    if height_f < 0.01 or height_f > 100000.0:
        raise ValueError("height must be between 0.01 and 100000")
    
    # Require min(width,height)-diameter > 1e-5
    min_dim = min(width_f, height_f)
    if min_dim - diameter_f <= 1e-5:
        raise ValueError("min(width,height) - diameter must be greater than 1e-5")
    
    if not value_f.is_integer():
        raise ValueError('Installed native stepover requires a whole percentage')
    return value_f
