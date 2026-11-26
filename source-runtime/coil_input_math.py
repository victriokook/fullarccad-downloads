import math


def resolve(mode, pitch, turns, height):
    def positive(value):
        try:value=float(value)
        except (ValueError,TypeError,OverflowError):raise ValueError('Expected a finite positive number') from None
        if not math.isfinite(value) or value<=0:raise ValueError('Expected a finite positive number')
        return value
    if mode=='pitch_turns':p,t=positive(pitch),positive(turns)
    elif mode=='height_turns':
        h,t=positive(height),positive(turns);p=h/t
    elif mode=='height_pitch':
        h,p=positive(height),positive(pitch);t=h/p
    else:raise ValueError('Unknown coil definition')
    if not (.001<=p<=100000 and .25<=t<=50 and .001<=p*t<=100000):
        raise ValueError('Coil pitch, turns or height out of range')
    return p,t
