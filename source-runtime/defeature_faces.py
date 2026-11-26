import re


def face_indices(names, face_count):
    if isinstance(face_count,bool) or not isinstance(face_count,int) or face_count<=0:raise ValueError('Invalid face count')
    if isinstance(names,(str,bytes)):raise ValueError('Expected a list of face names')
    try:names=list(names)
    except TypeError:raise ValueError('Expected a list of face names') from None
    if not 1<=len(names)<=200:raise ValueError('Select between1 and200 faces')
    seen=set();result=[]
    for name in names:
        if not isinstance(name,str) or re.fullmatch(r'Face[1-9][0-9]*',name) is None:raise ValueError('Invalid face name')
        index=int(name[4:])-1
        if index>=face_count or index in seen:raise ValueError('Missing or duplicate face')
        seen.add(index);result.append(index)
    return result
