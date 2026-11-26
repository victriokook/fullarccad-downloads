import math

def number(value,limit):
    if type(value) not in (int,float):raise ValueError('Expected builtin numeric input')
    try:value=float(value)
    except (OverflowError,ValueError):raise ValueError('Numeric conversion overflow') from None
    if not math.isfinite(value) or abs(value)>limit:raise ValueError('Nonfinite or out-of-range value')
    return value

def checked_offset(value):
    return number(value,1e6)

def station(parameter,first,last,edge_reversed,measure_reverse,offset=0):
    parameter,first,last=(number(value,1e7) for value in (parameter,first,last))
    if type(edge_reversed) is not bool or type(measure_reverse) is not bool:raise ValueError('Expected boolean direction')
    span=last-first
    if not 1e-7<span<=1e7:raise ValueError('Invalid path span')
    distance=last-parameter if edge_reversed else parameter-first
    if measure_reverse:distance=span-distance
    return number(distance+checked_offset(offset),1e7)
