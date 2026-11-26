"""Document-local view names, without filesystem semantics."""
def validate_name(name):
    if type(name) is not str or not 1<=len(name)<=64 or name!=name.strip():
        raise ValueError('Use1..64 characters without surrounding whitespace')
    if any(ord(c)<32 or ord(c)==127 or ord(c) in (0x2028,0x2029) or 0xD800<=ord(c)<=0xDFFF for c in name):
        raise ValueError('Control characters and invalid Unicode are excluded')
    return name


def renamed_entries(data, old_name, new_name):
    if type(data) is not dict:
        raise ValueError("data must be a dict")
    if len(data) < 1 or len(data) > 50:
        raise ValueError("data must have between 1 and 50 entries")
    
    try:
        validate_name(old_name)
        validate_name(new_name)
    except ValueError:
        raise ValueError("old_name and new_name are invalid")
    
    if old_name not in data:
        raise ValueError(f"missing old_name key: {old_name}")
    
    existing_new_names = set()
    for k in data:
        validate_name(k)
        existing_new_names.add(k)
    
    if new_name in existing_new_names and new_name != old_name:
        raise ValueError(f"duplicate new_name: {new_name}")
    
    result = {}
    for k, v in data.items():
        if k == old_name:
            result[new_name] = v
        else:
            result[k] = v
    
    return result
