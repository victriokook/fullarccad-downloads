import math
from japanese_solid_text import checked_text


def checked(text, height, tracking):
    if type(text) is not str:
        raise ValueError("text must be a string")
    if len(text) < 1 or len(text) > 20:
        raise ValueError("text length must be between 1 and 20 codepoints")
    if text.isspace():
        raise ValueError("text cannot be whitespace-only")
    checked_text(text)
    if type(height) not in (int,float):
        raise ValueError("height must be int or float")
    try:
        height = float(height)
    except OverflowError:
        raise ValueError("height conversion overflow")
    if not math.isfinite(height):
        raise ValueError("height is not finite")
    if not (0.1 <= height <= 1000):
        raise ValueError("height must be between 0.1 and 1000 inclusive")
    if type(tracking) not in (int,float):
        raise ValueError("tracking must be int or float")
    try:
        tracking = float(tracking)
    except OverflowError:
        raise ValueError("tracking conversion overflow")
    if not math.isfinite(tracking):
        raise ValueError("tracking is not finite")
    if not (-1000 <= tracking <= 1000):
        raise ValueError("tracking must be between -1000 and 1000 inclusive")
    return (text, height, tracking)


def checked_count(count):
    if type(count) is not int:
        raise ValueError("count must be an integer")
    try:
        count = int(count)
    except OverflowError:
        raise ValueError("count conversion overflow")
    if not (1 <= count <= 300):
        raise ValueError("count must be between 1 and 300 inclusive")
    return count
