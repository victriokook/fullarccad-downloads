"""Ordering for bounded sharp-point lofts; geometry is validated separately."""
def validate_points(kinds, closed=False):
    if type(kinds) not in (list, tuple) or not 2 <= len(kinds) <= 50:
        raise ValueError('Use 2..50 section kinds')
    if type(closed) is not bool:
        raise ValueError('closed must be boolean')
    if any(type(k) is not str or k not in ('wire', 'point') for k in kinds):
        raise ValueError('Each section must be wire or point')
    if 'wire' not in kinds:
        raise ValueError('At least one wire is required')
    if any(k == 'point' and (closed or i not in (0, len(kinds)-1))
           for i, k in enumerate(kinds)):
        raise ValueError('Points are allowed only at open loft endpoints')
    return tuple(kinds)
