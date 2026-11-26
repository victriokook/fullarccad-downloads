"""Canonical explicit face names, preserving user selection order."""
import re
def face_names(names,total):
    if type(total) is not int or not 1<=total<=100000:raise ValueError('Invalid face count.')
    if type(names) not in (list,tuple) or not 1<=len(names)<=200:raise ValueError('Select1–200 faces.')
    result=[]
    for name in names:
        if type(name) is not str or not re.fullmatch(r'Face[1-9][0-9]{0,5}',name) or int(name[4:])>total or name in result:raise ValueError('Use unique canonical FaceN names in range.')
        result.append(name)
    return tuple(result)
