import math
def check_frame(u_length, v_length, cross_length):
    if any(type(v) not in (int,float) for v in (u_length,v_length,cross_length)):raise ValueError('Use exact numeric types')
    if isinstance(u_length, bool) or isinstance(v_length, bool) or isinstance(cross_length, bool):
        raise ValueError("Boolean inputs not allowed")
    
    try:
        u_len = float(u_length)
        v_len = float(v_length)
        cross_len = float(cross_length)
    except (ValueError, OverflowError):
        raise ValueError("Inputs must be convertible to finite floats")
    
    if not all(math.isfinite(v) for v in (u_len,v_len,cross_len)):
        raise ValueError("Non-finite values detected")
    
    if u_length <= 1e-10:
        raise ValueError("u_length must be greater than 1e-10")
    if v_length <= 1e-10:
        raise ValueError("v_length must be greater than 1e-10")
    
    product=u_len*v_len
    if not math.isfinite(product):raise ValueError('Nonfinite derivative product')
    min_cross = 1e-8 * product
    if cross_length <= min_cross:
        raise ValueError("cross_length must be greater than 1e-8*u_length*v_length")
    
    return None
