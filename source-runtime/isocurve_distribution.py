def positions(count, single_fraction):
    if type(count) is not int or count < 1 or count > 50:
        raise ValueError("count must be an integer between 1 and 50 inclusive")
    
    if count == 1:
        return (single_fraction,)
    else:
        return tuple(i / (count + 1) for i in range(1, count + 1))
