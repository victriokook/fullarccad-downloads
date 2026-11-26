import math


def number(value, lower, upper):
    if type(value) is not int and type(value) is not float:
        raise ValueError("value must be int or float")
    
    try:
        fval = float(value)
    except (OverflowError, ValueError):
        raise ValueError("value cannot be converted to float")
    
    if math.isnan(fval) or math.isinf(fval):
        raise ValueError("value must be finite")
    
    if fval < lower or fval > upper:
        raise ValueError("value out of bounds")
    
    return fval


def flag(value):
    if type(value) is not bool:
        raise ValueError("value must be bool")
    return value


def direction(values):
    if type(values) not in (tuple, list):
        raise ValueError("values must be tuple or list")
    if len(values) != 3:
        raise ValueError("values must have exactly 3 elements")
    
    nums = []
    for v in values:
        nums.append(number(v, -1e6, 1e6))
    
    norm = math.sqrt(sum(x**2 for x in nums))
    if norm <= 1e-9:
        raise ValueError("norm too small")
    
    return tuple(x / norm for x in nums)
