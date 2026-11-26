import math

def validate_setup(margin, diameter, feed, plunge, rpm, tool_number):
    """
    Validate and normalize FreeCAD CAM setup parameters.
    
    Args:
        margin: float, 0..1000 mm
        diameter: float, 0.01..1000 mm
        feed: float, 0.01..100000 mm/min
        plunge: float, 0.01..100000 mm/min
        rpm: float, 1..100000 revolutions/min
        tool_number: int, 1..999
    
    Returns:
        dict with keys: margin, diameter, feed, plunge, rpm, tool_number
        Values are normalized to float (except tool_number which is int)
    
    Raises:
        ValueError: If any value is out of range, non-finite, or invalid type
    """
    # Helper to check finite and convert to float
    def to_finite_float(value, name):
        # Check if it's a bool first (bool is subclass of int)
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a numeric type, not bool")
        
        # Check if it's a string
        if isinstance(value, str):
            raise ValueError(f"{name} must be a numeric type, not string")
        
        # Check if it's a number
        if type(value) not in (int, float):
            raise ValueError(f"{name} must be a numeric type")
        
        # Convert to float
        try:
            fval = float(value)
        except (OverflowError, ValueError):
            raise ValueError(f"{name} cannot be converted to float")
        
        # Check for finite
        if not math.isfinite(fval):
            raise ValueError(f"{name} must be a finite number")
        
        return fval
    
    # Helper to check int range
    def to_int_in_range(value, name, min_val, max_val):
        # Check if it's a bool first
        if isinstance(value, bool):
            raise ValueError(f"{name} must be an int, not bool")
        
        # Check if it's an int
        if type(value) is not int:
            raise ValueError(f"{name} must be an int")
        
        if value < min_val or value > max_val:
            raise ValueError(f"{name} must be between {min_val} and {max_val}")
        
        return value
    
    # Validate margin: 0..1000 mm
    margin_f = to_finite_float(margin, "margin")
    if margin_f < 0 or margin_f > 1000:
        raise ValueError("margin must be between 0 and 1000")
    
    # Validate diameter: 0.01..1000 mm
    diameter_f = to_finite_float(diameter, "diameter")
    if diameter_f < 0.01 or diameter_f > 1000:
        raise ValueError("diameter must be between 0.01 and 1000")
    
    # Validate feed: 0.01..100000 mm/min
    feed_f = to_finite_float(feed, "feed")
    if feed_f < 0.01 or feed_f > 100000:
        raise ValueError("feed must be between 0.01 and 100000")
    
    # Validate plunge: 0.01..100000 mm/min
    plunge_f = to_finite_float(plunge, "plunge")
    if plunge_f < 0.01 or plunge_f > 100000:
        raise ValueError("plunge must be between 0.01 and 100000")
    
    # Validate rpm: 1..100000 revolutions/min
    rpm_f = to_finite_float(rpm, "rpm")
    if rpm_f < 1 or rpm_f > 100000:
        raise ValueError("rpm must be between 1 and 100000")
    
    # Validate tool_number: exact int 1..999
    tool_number_int = to_int_in_range(tool_number, "tool_number", 1, 999)
    
    # Return normalized dict
    return {
        "margin": margin_f,
        "diameter": diameter_f,
        "feed": feed_f,
        "plunge": plunge_f,
        "rpm": rpm_f,
        "tool_number": tool_number_int
    }
