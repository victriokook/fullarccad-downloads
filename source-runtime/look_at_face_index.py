def face_index(name, count):
    if type(count) is not int:
        raise ValueError("count must be an integer")
    if count < 1 or count > 100000:
        raise ValueError("count must be between 1 and 100000")
    if type(name) is not str:
        raise ValueError("name must be a string")
    if len(name) > 10:
        raise ValueError("name length exceeds limit")
    if not name.startswith("Face") or not name[4:] or any(c not in "0123456789" for c in name[4:]) or name[4:][0]=="0":
        raise ValueError("name must be canonical ASCII FaceN")
    index=int(name[4:])
    if not 1<=index<=count:raise ValueError("Face index outside shape")
    return index-1
