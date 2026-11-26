import math


def fractions(forward, backward, closed):
    # Validate types: must be exact builtin int or float
    if type(forward) not in (int, float):
        raise ValueError("forward must be exact builtin int or float")
    if type(backward) not in (int, float):
        raise ValueError("backward must be exact builtin int or float")
    if type(closed) is not bool:
        raise ValueError("closed must be exact builtin bool")

    # Reject bool numeric arguments for forward and backward
    if isinstance(forward, bool):
        raise ValueError("forward cannot be a bool")
    if isinstance(backward, bool):
        raise ValueError("backward cannot be a bool")

    # Convert to float for arithmetic, checking for overflow from huge integers first
    try:
        f_val = float(forward)
    except (OverflowError, ValueError):
        raise ValueError("forward conversion failed or caused overflow")

    try:
        b_val = float(backward)
    except (OverflowError, ValueError):
        raise ValueError("backward conversion failed or caused overflow")

    # Check finiteness
    if not math.isfinite(f_val):
        raise ValueError("forward must be finite")
    if not math.isfinite(b_val):
        raise ValueError("backward must be finite")

    # Range checks: 0.001 <= forward <= 1
    if f_val < 0.001 or f_val > 1.0:
        raise ValueError("forward must satisfy 0.001 <= forward <= 1")

    # Range checks for backward: either zero or 0.001 <= backward <= 1
    if b_val != 0.0:
        if b_val < 0.001 or b_val > 1.0:
            raise ValueError("nonzero backward must satisfy 0.001 <= backward <= 1")

    # Logic: Reject nonzero backward unless closed is True
    if b_val != 0.0 and not closed:
        raise ValueError("nonzero backward is only allowed when closed is True")

    # Sum check: forward + backward must not exceed 1 (no tolerances, no clamping)
    if f_val + b_val > 1.0:
        raise ValueError("forward + backward must not exceed 1")

    return (f_val, b_val)
