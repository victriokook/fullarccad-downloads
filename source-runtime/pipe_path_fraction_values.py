"""Validated forward arc-length fraction; no-path pipes retain full length."""
import math

def fraction(value):
    if type(value) not in (int,float):
        raise ValueError('Path fraction requires a number')
    try:
        result=float(value)
    except (OverflowError,ValueError):
        raise ValueError('Path fraction must be finite') from None
    if not math.isfinite(result) or not .001<=result<=1:
        raise ValueError('Path fraction must be .001..1')
    return result

def effective_fraction(value,has_path):
    if type(has_path) is not bool:
        raise ValueError('has_path requires an exact bool')
    result=fraction(value)
    if not has_path and result!=1:
        raise ValueError('A path is required for a partial pipe')
    return result
