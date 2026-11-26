import math

def center_coordinates(values):
    try:
        if len(values) != 3 or any(isinstance(v, bool) for v in values):
            raise ValueError("Exactly 3 non-bool values required")
        nums = [float(v) for v in values]
        if not all(math.isfinite(v) for v in nums):raise ValueError("Finite center coordinates required")
        return tuple(nums)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Invalid center coordinates") from error
