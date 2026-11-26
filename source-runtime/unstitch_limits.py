def face_limit(count):
    if isinstance(count, bool) or not isinstance(count, int): raise ValueError("count must be int but not bool")
    if count < 2 or count > 200: raise ValueError("count must be between 2 and 200 inclusive")
    return count
