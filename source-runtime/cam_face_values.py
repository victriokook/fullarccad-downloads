def validate_face_depth(start, final, model_top, stock_top):
    """
    Validate face depth parameters.
    
    Parameters:
    start: float, starting Z position (must be >= stock_top)
    final: float, final Z position (must be < stock_top and >= model_top)
    model_top: float, top of the model
    stock_top: float, top of the stock material
    
    Returns:
    dict: {'start': float, 'final': float}
    
    Raises:
    ValueError: If any parameter is invalid
    """
    # Check that all inputs are int or float (not bool, not subclasses)
    def check_type(value, name):
        if isinstance(value, bool):
            raise ValueError(f"{name} must be int or float, not bool")
        if type(value) not in (int, float):
            raise ValueError(f"{name} must be int or float")
        if isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf')):
            raise ValueError(f"{name} must be finite")
        if isinstance(value, int) and abs(value) > 1e6:
            raise ValueError(f"{name} is too large: {value}")
        if isinstance(value, float) and abs(value) > 1e6:
            raise ValueError(f"{name} is too large: {value}")
        return float(value)
    
    start = check_type(start, "start")
    final = check_type(final, "final")
    model_top = check_type(model_top, "model_top")
    stock_top = check_type(stock_top, "stock_top")
    
    # Validate constraints
    if final < model_top:
        raise ValueError(f"final ({final}) must be >= model_top ({model_top})")
    
    if final >= stock_top:
        raise ValueError(f"final ({final}) must be < stock_top ({stock_top})")
    
    if start < stock_top:
        raise ValueError(f"start ({start}) must be >= stock_top ({stock_top})")
    
    if start <= final:
        raise ValueError(f"start ({start}) must be > final ({final})")
    
    if (start - final) > 100:
        raise ValueError(f"start - final ({start - final}) must be <= 100")
    
    return {'start': start, 'final': final}
