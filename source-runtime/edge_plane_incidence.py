import math
def check_incidence(dot):
    try:
        if type(dot) not in (int,float) or not math.isfinite(dot) or not 1e-7<=abs(dot)<=1.000000000001:raise ValueError("Use a finite nonparallel direction cosine")
    except OverflowError as error:raise ValueError("Direction cosine overflow") from error
    return dot
