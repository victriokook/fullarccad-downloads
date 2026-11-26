import math

def direction(values):
    try:
        items = tuple(values)
        if len(items) != 3 or any(isinstance(v, bool) for v in items):
            raise ValueError("Three non-boolean coordinates required")
        result = tuple(float(v) for v in items)
        if not all(math.isfinite(v) for v in result):
            raise ValueError("Finite coordinates required")
        norm = math.hypot(*result)
        if norm < 1e-12 or not math.isfinite(norm):
            raise ValueError("Invalid direction magnitude")
        return tuple(v / norm for v in result)
    except (TypeError, OverflowError, ValueError) as exc:
        raise ValueError("Invalid projection direction") from exc
