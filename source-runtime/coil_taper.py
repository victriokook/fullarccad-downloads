"""Reviewed local-Qwen radius helper; staged research, not adopted runtime."""
import math

def taper_radius(radius, height, angle):
    for value in (radius, height, angle):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Expected finite numeric inputs')
        if not math.isfinite(value):
            raise ValueError('Expected finite numeric inputs')
    if radius <= 0 or height <= 0 or not -45 <= angle <= 45:
        raise ValueError('Invalid radius, height or angle')
    result = radius + height * math.tan(math.radians(angle))
    if not math.isfinite(result) or result <= 0:
        raise ValueError('Taper reaches or crosses the axis')
    return result


def spine(pitch, turns, radius, angle, left):
    import Part
    height = pitch * turns
    taper_radius(radius, height, angle)
    # Keep the accepted cylindrical path byte-for-byte equivalent in behavior.
    if angle == 0:
        return Part.Wire(Part.makeHelix(pitch, height, radius, 0, left).Edges)
    # makeLongHelix supports signed conical angles and axial pitch/height.
    # Plain makeHelix ignores negative angles and defaults to slant height.
    return Part.Wire(Part.makeLongHelix(pitch, height, radius, angle, left).Edges)
