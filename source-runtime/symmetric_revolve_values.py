def validate(angle, symmetric):
    if type(symmetric) is not bool:
        raise ValueError("symmetric must be exact bool")
    
    if type(angle) not in (int,float):
        raise ValueError("angle cannot be bool")
    
    if isinstance(angle, str):
        raise ValueError("angle cannot be string")
    
    try:
        float_angle = float(angle)
    except (OverflowError, ValueError):
        raise ValueError("Invalid angle value")
    
    if not (0 < float_angle <= 360):
        raise ValueError("angle must be between 0 and 360 exclusive of 0 inclusive of 360")
    
    return float_angle, symmetric
