def validate(closed, section_count):
    if type(closed) is not bool:
        raise ValueError("closed must be a boolean")
    if type(section_count) is not int or isinstance(section_count, bool):
        raise ValueError("section_count must be an integer (not a boolean)")
    
    if closed is False:
        if section_count < 2:
            raise ValueError("At least 2 sections are required when closed is False")
    elif closed is True:
        if section_count < 3 or section_count > 50:
            raise ValueError("When closed is True, section_count must be between 3 and 50 inclusive")
    
    return closed
