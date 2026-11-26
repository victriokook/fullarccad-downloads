def validate_linked(value, editing=False):
    if type(value) is not bool:
        raise ValueError("value must be a boolean")
    if type(editing) is not bool:
        raise ValueError("editing must be a boolean")
    if editing and not value:
        raise ValueError("independent curves can only be created as new objects and existing linked features are not detached")
    return value
