from single_face_input import single_face

def is_single_face(shape):
    try:
        return bool(single_face(shape))
    except (ValueError, RuntimeError, AttributeError):
        return False
