import re

def checked_element(name, edge_count, face_count):
    for count in (edge_count,face_count):
        if type(count) is not int or not 0<=count<=1000000:
            raise ValueError('Element count must be a builtin integer in range')
    if type(name) is not str or len(name)>20:
        raise ValueError('Canonical EdgeN or FaceN required')
    match=re.fullmatch(r'(Edge|Face)([1-9][0-9]*)',name)
    if match is None:raise ValueError('Canonical ASCII EdgeN or FaceN required')
    kind=match.group(1)
    if int(match.group(2))>(edge_count if kind=='Edge' else face_count):
        raise ValueError('Direction element is out of range')
    return kind
