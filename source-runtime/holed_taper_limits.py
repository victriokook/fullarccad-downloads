def validate_counts(wires, edges):
    if type(wires) is not int:
        raise ValueError("wires must be an integer")
    if type(edges) is not int:
        raise ValueError("edges must be an integer")
    if wires < 1 or wires > 51:
        raise ValueError("wires must be between 1 and 51")
    if edges < 1 or edges > 200:
        raise ValueError("edges must be between 1 and 200")
    return wires - 1
