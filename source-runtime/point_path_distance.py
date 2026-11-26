import math

def distance_on_edge(length, mode, value, reverse=False):
    if isinstance(length,bool) or not isinstance(length, (int, float)) or length <= 1e-9:
        raise ValueError("length must be positive finite")
    if isinstance(value,bool) or not isinstance(value, (int, float)):
        raise ValueError("value must be numeric")
    if not isinstance(reverse, bool):
        raise ValueError("reverse must be boolean")
    if mode not in ("fraction", "distance"):
        raise ValueError("mode must be 'fraction' or 'distance'")
    if math.isnan(length) or math.isinf(length):
        raise ValueError("length cannot be NaN or inf")
    if math.isnan(value) or math.isinf(value):
        raise ValueError("value cannot be NaN or inf")
    if mode == "fraction":
        if not (0 <= value <= 1):
            raise ValueError("fraction value must be between 0 and 1")
        result = length * value
    else:
        if not (0 <= value <= length):
            raise ValueError("distance value must be between 0 and length")
        result = value
    if reverse:
        return length - result
    return result
