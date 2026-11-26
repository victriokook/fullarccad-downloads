def checked_facets(value):
    if type(value) is not int or not 1<=value<=2000:
        raise ValueError('Facet count must be1..2000')
    return value
