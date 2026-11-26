def checked_counts(counts):
    if type(counts) not in (list,tuple) or not 2<=len(counts)<=20 or any(type(n) is not int or n<1 for n in counts) or sum(counts)>20000:
        raise ValueError('Use2..20 meshes with1..20000 total facets')
    return tuple(counts)
