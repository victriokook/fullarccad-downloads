"""Validated cumulative arc-length location; no CAD dependencies."""
import math


def locate_segment(lengths, distance):
    if type(lengths) not in (list, tuple) or not 1 <= len(lengths) <= 200:
        raise ValueError('Choose 1..200 segment lengths')
    try:
        if type(distance) not in (int, float) or not math.isfinite(distance):
            raise ValueError('Distance must be finite numeric')
        if any(type(length) not in (int, float) or not math.isfinite(length) or length <= 1e-9 for length in lengths):
            raise ValueError('Lengths must be positive finite numeric')
        total = math.fsum(lengths)
    except OverflowError as error:
        raise ValueError('Arc length overflow') from error
    if not math.isfinite(total) or not 0 <= distance <= total:
        raise ValueError('Distance must fit the path')
    if distance == total:
        return len(lengths)-1, lengths[-1]
    before = 0.0
    for index, length in enumerate(lengths):
        after = math.fsum(lengths[:index+1])
        if distance <= after:
            return index, min(length, max(0.0, distance-before))
        before = after
    raise ValueError('Distance exceeds the path')
