import math
def checked(iterations,strength):
    if type(iterations) is not int or not 1<=iterations<=20:raise ValueError('Iterations must be1..20')
    if type(strength) not in (int,float):raise ValueError('Expected strength number')
    try:value=float(strength)
    except OverflowError:raise ValueError('Overflow')
    if not math.isfinite(value) or not .01<=value<=.5:raise ValueError('Strength must be.01...5')
    return iterations,value
