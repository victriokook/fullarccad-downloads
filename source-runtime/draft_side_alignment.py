import math
def check_side_alignment(kind, dot):
    if not isinstance(kind, str) or kind not in ("plane", "cylinder"):
        raise ValueError("kind must be 'plane' or 'cylinder'")
    if isinstance(dot, bool) or not isinstance(dot,(int,float)):
        raise ValueError("dot must be int or float, not bool")
    try:
        dot = float(dot)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("dot must be convertible to float")
    if not math.isfinite(dot) or abs(dot) > 1 + 1e-12:
        raise ValueError("abs(dot) must be <= 1 + 1e-12")
    if kind == "plane":
        if abs(dot) > 1e-7:
            raise ValueError("For plane, abs(dot) must be <= 1e-7")
    elif kind == "cylinder":
        if abs(abs(dot) - 1.0) > 1e-7:
            raise ValueError("For cylinder, abs(abs(dot)-1) must be <= 1e-7")
    return None
