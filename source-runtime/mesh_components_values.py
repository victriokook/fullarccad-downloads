def checked(threshold, facets):
    if type(threshold) is not int or isinstance(threshold, bool):
        raise ValueError("threshold must be exact builtin int")
    if type(facets) is not int or isinstance(facets, bool):
        raise ValueError("facets must be exact builtin int")
    if not (1 <= threshold <= 20000):
        raise ValueError("threshold out of range 1..20000")
    if not (1 <= facets <= 20000):
        raise ValueError("facets out of range 1..20000")
    return threshold


def partition(counts, threshold):
    if type(counts) not in (list, tuple):
        raise ValueError("counts must be list or tuple")
    if len(counts) == 0:
        raise ValueError("counts must have 1..20000 elements")
    if len(counts) > 20000:
        raise ValueError("counts length out of range 1..20000")
    
    total = 0
    for c in counts:
        if type(c) is not int or isinstance(c, bool):
            raise ValueError("each count must be exact builtin int")
        if c < 1:
            raise ValueError("each count must be >= 1")
        total += c
    
    if total > 20000:
        raise ValueError("total count exceeds 20000")
    
    threshold = checked(threshold, total)
    
    retained_indices = []
    removed_indices = []
    
    for i, c in enumerate(counts):
        if c <= threshold:
            removed_indices.append(i)
        else:
            retained_indices.append(i)
    
    if not removed_indices:
        raise ValueError("none removed")
    if not retained_indices:
        raise ValueError("none retained")
    
    return (tuple(retained_indices), tuple(removed_indices))
