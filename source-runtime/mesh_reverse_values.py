def sample_indices(count):
    if type(count) is not int or not 1<=count<=20000:raise ValueError('Facet count must be1..20000')
    step=(count+199)//200
    return tuple(range(0,count,step))
