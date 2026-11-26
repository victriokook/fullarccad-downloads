from rectangular_direction_values import checked_direction
import math

def independent_directions(first, second):
    first_unit = checked_direction(first)
    second_unit = checked_direction(second)
    cross_x = first_unit[1] * second_unit[2] - first_unit[2] * second_unit[1]
    cross_y = first_unit[2] * second_unit[0] - first_unit[0] * second_unit[2]
    cross_z = first_unit[0] * second_unit[1] - first_unit[1] * second_unit[0]
    cross_length = math.hypot(cross_x, cross_y, cross_z)
    if cross_length < 1e-7:
        raise ValueError("Cross product length is too small")
    return (first_unit, second_unit)

def resolve_second_mode(value, current=False):
    if type(current) is not bool:
        raise ValueError("current must be a boolean")
    if value is None:
        return current
    if type(value) is not bool:
        raise ValueError("value must be a boolean")
    return value
