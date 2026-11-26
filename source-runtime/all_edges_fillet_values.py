def checked_radius(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("radius must be int or float excluding bool")
    try:
        radius = float(value)
    except OverflowError:
        raise ValueError("radius value too large to convert")
    if not (0.001 <= radius <= 100000):
        raise ValueError("radius must be between 0.001 and 100000 inclusive")
    return float(radius)

def checked_edge_count(value):
    if type(value) is not int:
        raise ValueError("edge_count must be exact int excluding bool")
    if not (1 <= value <= 200):
        raise ValueError("edge_count must be between 1 and 200 inclusive")
    return value
