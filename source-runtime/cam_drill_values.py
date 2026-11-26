def validate_drill_depths(start, final, retract, clearance):
    """
    Validate drilling parameters for G81 cycle.
    
    Args:
        start: Starting height (Z)
        final: Final drilling depth (Z)
        retract: Retract height (Z)
        clearance: Clearance height (Z)
        
    Returns:
        dict with keys 'start', 'final', 'retract', 'clearance' as floats
        
    Raises:
        ValueError: If any input is invalid
    """
    
    def validate_single_value(value, name):
        """Validate a single numeric value."""
        # Check for bool first (bool is subclass of int in Python)
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a number, not bool")
        
        # Check for int or float
        if type(value) not in (int, float):
            raise ValueError(f"{name} must be an int or float, got {type(value).__name__}")
        
        # Check for finite (not inf or nan)
        if isinstance(value, float):
            if value != value:  # NaN check
                raise ValueError(f"{name} must be finite, got NaN")
            if value == float('inf') or value == float('-inf'):
                raise ValueError(f"{name} must be finite, got {value}")
        elif isinstance(value, int):
            # Giant integers are allowed as long as they fit in float range for abs check
            pass
        
        # Check abs <= 1e6
        if abs(value) > 1e6:
            raise ValueError(f"abs({name}) must be <= 1e6, got {abs(value)}")
        
        return float(value)
    
    # Validate all inputs
    start_val = validate_single_value(start, "start")
    final_val = validate_single_value(final, "final")
    retract_val = validate_single_value(retract, "retract")
    clearance_val = validate_single_value(clearance, "clearance")
    
    # Check depth >= 0.001 (drill depth is start - final, must be at least 0.001)
    drill_depth = start_val - final_val
    if drill_depth < 0.001:
        raise ValueError(f"Drill depth (start - final) must be >= 0.001, got {drill_depth}")
    
    # Check final < start
    if not (final_val < start_val):
        raise ValueError(f"final ({final_val}) must be less than start ({start_val})")
    
    # Check start <= retract
    if not (start_val <= retract_val):
        raise ValueError(f"start ({start_val}) must be <= retract ({retract_val})")
    
    # Check retract <= clearance
    if not (retract_val <= clearance_val):
        raise ValueError(f"retract ({retract_val}) must be <= clearance ({clearance_val})")
    
    # Check retract > start (strictly greater)
    if not (retract_val > start_val):
        raise ValueError(f"retract ({retract_val}) must be strictly greater than start ({start_val})")
    
    return {
        'start': start_val,
        'final': final_val,
        'retract': retract_val,
        'clearance': clearance_val
    }
