import math
def validate_text_values(text, size, tracking, depth):
    from japanese_solid_text import checked_text
    text=checked_text(text)
    if isinstance(size, bool) or isinstance(tracking, bool) or isinstance(depth, bool):
        raise ValueError("Numeric arguments must not be booleans.")
    try:
        size_f = float(size)
        tracking_f = float(tracking)
        depth_f = float(depth)
    except (TypeError, OverflowError, ValueError):
        raise ValueError("Numeric arguments must be convertible to finite floats.")
    if not isinstance(size, (int, float)) or not math.isfinite(size_f):
        raise ValueError("Size must be a finite number.")
    if not isinstance(tracking, (int, float)) or not math.isfinite(tracking_f):
        raise ValueError("Tracking must be a finite number.")
    if not isinstance(depth, (int, float)) or not math.isfinite(depth_f):
        raise ValueError("Depth must be a finite number.")
    if size_f < 0.1 or size_f > 1000:
        raise ValueError("Size must be between 0.1 and 1000.")
    if tracking_f < -1000 or tracking_f > 1000:
        raise ValueError("Tracking must be between -1000 and 1000.")
    if depth_f < 0.001 or depth_f > 1000:
        raise ValueError("Depth must be between 0.001 and 1000.")
    return text, size_f, tracking_f, depth_f
