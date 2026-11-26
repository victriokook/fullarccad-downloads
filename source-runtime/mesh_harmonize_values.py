def winding_key(face):
    if type(face) not in (list,tuple) or len(face)!=3 or any(type(v) is not int or v<0 for v in face) or len(set(face))!=3:
        raise ValueError('Invalid triangle')
    a,b,c=face
    return min((a,b,c),(b,c,a),(c,a,b))

def changed_indices(before,after):
    if type(before) not in (list,tuple) or type(after) not in (list,tuple) or not 2<=len(before)<=20000 or len(before)!=len(after):raise ValueError('Invalid triangle counts')
    changed=[]
    for i,(a,b) in enumerate(zip(before,after)):
        left,right=winding_key(a),winding_key(b)
        if sorted(left)!=sorted(right):raise ValueError('Triangle vertices changed')
        if left!=right:changed.append(i)
    return tuple(changed)
