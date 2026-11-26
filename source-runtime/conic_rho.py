def conic_weight(rho):
    if isinstance(rho, bool):
        raise ValueError("rho must not be a bool")
    if not isinstance(rho, (int, float)):
        raise ValueError("rho must be int or float")
    try:
        rho_f = float(rho)
    except (OverflowError, ValueError):
        raise ValueError("rho conversion failed")
    if rho_f != rho_f:
        raise ValueError("rho must be finite")
    if abs(rho_f) > 1e308:
        raise ValueError("rho is oversized")
    if rho_f < 0.001 or rho_f > 0.999:
        raise ValueError("rho must be within .001.. .999 inclusive")
    return rho_f / (1.0 - rho_f)
