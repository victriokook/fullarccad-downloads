"""Signed distance along the canonical source face normal, independent of Reverse."""
import math

def checked_offset(value):
    if type(value) not in (int,float):
        raise ValueError('Start offset requires a built-in number')
    try:
        result=float(value)
    except OverflowError:
        raise ValueError('Start offset must be finite') from None
    if not math.isfinite(result) or not -100000<=result<=100000:
        raise ValueError('Start offset must be within +/-100000mm')
    return result

def resolve_offset(value,previous=0.):
    return checked_offset(previous if value is None else value)
