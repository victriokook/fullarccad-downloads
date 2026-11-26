def validate_options(count,ruled=False,closed=False):
    if type(count) is not int or not 2<=count<=20:raise ValueError('Surface loft requires 2..20 sections')
    if type(ruled) is not bool:raise ValueError('Ruled must be a builtin bool')
    if type(closed) is not bool or closed:raise ValueError('Closed-loop surface loft is not supported')
    return count,ruled,closed
