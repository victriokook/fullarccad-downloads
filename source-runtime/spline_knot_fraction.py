import math

def checked_fraction(value):
    if isinstance(value, bool):
        raise ValueError("Boolean values are not accepted")
    if isinstance(value, float):
        try:
            result = float(value)
        except OverflowError:
            raise ValueError("Overflow occurred during conversion")
        if not math.isfinite(result):
            raise ValueError("Value must be finite")
        if not (0.001 <= result <= 0.999):
            raise ValueError("Value must be between 0.001 and 0.999 inclusive")
        return result
    elif isinstance(value, int):
        try:
            result = float(value)
        except OverflowError:
            raise ValueError("Overflow occurred during conversion")
        if not math.isfinite(result):
            raise ValueError("Value must be finite")
        if not (0.001 <= result <= 0.999):
            raise ValueError("Value must be between 0.001 and 0.999 inclusive")
        return result
    else:
        raise ValueError("Value must be int or float")

def new_parameter(fraction, first, last, knots):
    fraction = checked_fraction(fraction)
    
    def numeric(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)):
            raise ValueError("Parameter must be numeric")
        try:value=float(value)
        except OverflowError:raise ValueError("Parameter overflow")
        if not math.isfinite(value):raise ValueError("Parameter must be finite")
        return value
    first,last=numeric(first),numeric(last)

    if not (last > first):
        raise ValueError("last must be greater than first")
    
    span = last - first
    if not math.isfinite(span):
        raise ValueError("Span is not finite")
    
    p = first + span * fraction
    if not math.isfinite(p):
        raise ValueError("Resulting parameter is not finite")
    
    if isinstance(knots, (list, tuple)):
        for knot in knots:
            if not isinstance(knot, (int, float)) or isinstance(knot, bool):
                raise ValueError("Knots must be a list/tuple of finite numeric values")
            try:
                k = float(knot)
            except OverflowError:
                raise ValueError("Overflow occurred for a knot value")
            if not math.isfinite(k):
                raise ValueError("Knot values must be finite")
            
            normalized_k = (k - first) / span
            if not math.isfinite(normalized_k):raise ValueError("Normalized knot overflow")
            if abs(normalized_k - fraction) <= 1e-7:
                raise ValueError("Existing knot found at this parameter")
    else:
        raise ValueError("Knots must be a list or tuple")
    
    return p
