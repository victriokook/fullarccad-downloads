def checked_count(value):
    if type(value) is not int or not 3<=value<=200:
        raise ValueError('Maximum boundary edges must be3..200')
    return value
