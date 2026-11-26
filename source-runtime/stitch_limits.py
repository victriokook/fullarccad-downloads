def validate_face_count(count):
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError("Invalid type")
    if count < 2 or count > 200:
        raise ValueError("Out of range")
    return count
