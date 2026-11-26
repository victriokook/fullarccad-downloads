import math


def validate_depths(start, final, step, safe, clearance):
    """
    Validate parameters for CAM path generation.
    
    Parameters:
    start, final, step, safe, clearance: numeric values (int or float, not bool)
    
    Returns:
    dict: Validated parameters as floats
    
    Raises:
    ValueError: If any validation fails
    """
    # Helper function to validate and convert a single parameter
    def validate_param(value, name):
        # Reject bool and subclasses
        if isinstance(value, bool):
            raise ValueError(f"{name} must not be a boolean")
        
        # Check if it's int or float (but not bool, which is subclass of int)
        if type(value) not in (int, float):
            raise ValueError(f"{name} must be int or float")
        
        # Convert to float
        try: result = float(value)
        except OverflowError: raise ValueError("Numeric overflow")
        
        # Check for infinity
        if math.isinf(result):
            raise ValueError(f"{name} must be finite")
        
        # Check for NaN
        if math.isnan(result):
            raise ValueError(f"{name} must be finite")
        
        # Check absolute value constraint
        if abs(result) > 1000000:
            raise ValueError(f"abs({name}) must be <= 1000000")
        
        return result
    
    # Validate all parameters
    start_val = validate_param(start, "start")
    final_val = validate_param(final, "final")
    step_val = validate_param(step, "step")
    safe_val = validate_param(safe, "safe")
    clearance_val = validate_param(clearance, "clearance")
    
    # Check step >= 0.001
    if step_val < 0.001:
        raise ValueError("step must be >= 0.001")
    
    # Check final < start < safe <= clearance
    if not (final_val < start_val < safe_val <= clearance_val):
        raise ValueError("Invalid order: final < start < safe <= clearance")
    
    # Check ceil((start-final)/step) <= 200
    num_steps = math.ceil((start_val - final_val) / step_val)
    if num_steps > 200:
        raise ValueError(f"Number of steps ({num_steps}) exceeds maximum of 200")
    
    # Return dict with float values
    return {
        'start': start_val,
        'final': final_val,
        'step': step_val,
        'safe': safe_val,
        'clearance': clearance_val
    }
