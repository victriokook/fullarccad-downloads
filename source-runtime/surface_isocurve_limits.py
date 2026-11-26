def validate_complexity(u_poles, v_poles, u_degree, v_degree):
    if isinstance(u_poles, bool) or isinstance(v_poles, bool) or \
       isinstance(u_degree, bool) or isinstance(v_degree, bool):
        raise ValueError("All inputs must be integers, not booleans.")
    
    if any(type(v) is not int for v in (u_poles,v_poles,u_degree,v_degree)):
        raise ValueError("All inputs must be integers.")
    
    if u_poles < 2 or u_poles > 50:
        raise ValueError("u_poles must be between 2 and 50 inclusive.")
    if v_poles < 2 or v_poles > 50:
        raise ValueError("v_poles must be between 2 and 50 inclusive.")
    
    if u_poles * v_poles > 2500:
        raise ValueError("Product of pole counts must not exceed 2500.")
    
    if u_degree < 1 or u_degree > 9:
        raise ValueError("u_degree must be between 1 and 9 inclusive.")
    if v_degree < 1 or v_degree > 9:
        raise ValueError("v_degree must be between 1 and 9 inclusive.")
    
    if u_degree >= u_poles:
        raise ValueError("u_degree must be strictly less than u_poles.")
    if v_degree >= v_poles:
        raise ValueError("v_degree must be strictly less than v_poles.")
    
    return None
