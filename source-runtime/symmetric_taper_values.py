import math
def validate_extent(mode, height, angle, second_height, second_angle):
    if type(mode) is not str or mode not in ('sides', 'symmetric_half', 'symmetric_whole'):
        raise ValueError("mode must be 'sides', 'symmetric_half', or 'symmetric_whole'")
    
    if type(height) not in (int, float):
        raise ValueError("height must be a finite number")
    try:
        height = float(height)
    except (ValueError, OverflowError):
        raise ValueError("height conversion failed")
    
    if type(angle) not in (int, float):
        raise ValueError("angle must be a finite number")
    try:
        angle = float(angle)
    except (ValueError, OverflowError):
        raise ValueError("angle conversion failed")
    
    if type(second_height) not in (int, float):
        raise ValueError("second_height must be a finite number")
    try:
        second_height = float(second_height)
    except (ValueError, OverflowError):
        raise ValueError("second_height conversion failed")
    
    if type(second_angle) not in (int, float):
        raise ValueError("second_angle must be a finite number")
    try:
        second_angle = float(second_angle)
    except (ValueError, OverflowError):
        raise ValueError("second_angle conversion failed")
    
    if not all(math.isfinite(v) for v in (height,angle,second_height,second_angle)):
        raise ValueError("All values must be finite")
    if not -45 <= second_angle <= 45:
        raise ValueError("Opposite angle out of range")
    if height < 0.001 or height > 100000:
        raise ValueError("height must be between 0.001 and 100000")
    
    if angle < -45 or angle > 45:
        raise ValueError("angle must be between -45 and 45")
    
    if second_height == 0:
        if second_angle != 0:
            raise ValueError("zero second_height requires zero second_angle")
        second_angle = 0.0
    elif second_height < 0.001 or second_height > 100000:
        raise ValueError("second_height must be 0 or between 0.001 and 100000")
    
    
    if mode == 'sides':
        return (height, second_height, second_angle, False)
    
    elif mode in ('symmetric_half', 'symmetric_whole'):
        if second_height != 0 or second_angle != 0:
            raise ValueError("Symmetric modes require second_height and second_angle both zero")
        
        native_forward = height * 2 if mode == 'symmetric_half' else height
        
        if native_forward > 100000:
            raise ValueError("native_forward exceeds 100000")
        
        return (native_forward, 0, angle, True)
