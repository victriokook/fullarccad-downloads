def internal_count(wire_count):
    if isinstance(wire_count, bool) or not isinstance(wire_count, int) or wire_count < 2 or wire_count > 201:
        raise ValueError("wire_count must be an integer between 2 and 201 inclusive")
    return wire_count - 1
