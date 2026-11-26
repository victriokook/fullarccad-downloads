def check_radius(min_radius, reach, angle):
    import math
    
    if any(type(v) not in (int,float) for v in (min_radius,reach,angle)):raise ValueError('Use exact numeric types')
    try:min_radius,reach,angle=map(float,(min_radius,reach,angle))
    except (ValueError,OverflowError):raise ValueError('Finite values required')
    # Check for non-finite values (inf, nan)
    if not math.isfinite(min_radius):
        raise ValueError("min_radius must be finite")
    if not math.isfinite(reach):
        raise ValueError("reach must be finite")
    if not math.isfinite(angle):
        raise ValueError("angle must be finite")
    
    # Check string subclasses for bool (if passed as strings like "True", "False")
    if isinstance(min_radius, str) or isinstance(reach, str) or isinstance(angle, str):
        raise ValueError("Inputs must not be string subclasses")
    
    # Validate min_radius > 1e-6
    if min_radius <= 1e-6:
        raise ValueError("min_radius must be greater than 1e-6")
    
    # Validate reach > 0
    if reach <= 0:
        raise ValueError("reach must be greater than 0")
    
    # Validate 0 < angle <= 45
    if not (0 < angle <= 45):
        raise ValueError("angle must be between 0 and 45 inclusive")
    
    # Convert angle to radians
    rad_angle = math.radians(angle)
    
    # Calculate reach * tan(radians(angle))
    try:
        tangent_value = math.tan(rad_angle)
        product = reach * tangent_value
    except OverflowError:
        raise ValueError("Nonfinite product detected")
    
    # Check if product is non-finite
    if not math.isfinite(product):
        raise ValueError("Nonfinite product detected")
    
    # Validate condition: reject if reach*tan(radians(angle)) >= min_radius - max(1e-7, min_radius*1e-9)
    threshold = min_radius - max(1e-7, min_radius * 1e-9)
    if product >= threshold:raise ValueError('Cone draft radius could collapse')
    return None
