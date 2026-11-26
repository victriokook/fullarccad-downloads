import re
def checked_cells(value, count, count2):
    if type(count) is not int or count < 1:
        raise ValueError("count must be exact int >= 1")
    if type(count2) is not int or count2 < 1:
        raise ValueError("count2 must be exact int >= 1")
    if count * count2 > 200:
        raise ValueError("product of counts must be <= 200")
    
    if type(value) not in (list, tuple):
        raise ValueError("value must be tuple or list")
    if len(value) > 199:
        raise ValueError("value must have at most 199 entries")
    
    valid_cells = set()
    for i, entry in enumerate(value):
        if type(entry) not in (list, tuple):
            raise ValueError(f"Entry {i} must be tuple or list")
        if len(entry) != 2:
            raise ValueError(f"Entry {i} must have length 2")
        
        c, r = entry[0], entry[1]
        
        if type(c) is not int:
            raise ValueError(f"Column at {i} must be exact int")
        if type(r) is not int:
            raise ValueError(f"Row at {i} must be exact int")
        
        if c < 1 or r < 1:
            raise ValueError("Coordinates must be >= 1")
        if c > count or r > count2:
            raise ValueError(f"Coordinate ({c}, {r}) out of range")
        
        if (c,r)==(1,1):
            raise ValueError("Original cell cannot be suppressed")
        cell_key = (c, r)
        if cell_key in valid_cells:
            raise ValueError("Duplicate cells not allowed")
        valid_cells.add(cell_key)
    
    result = tuple(sorted(valid_cells,key=__import__('builtins')._fullarc_qt_slot(lambda cell:(cell[1],cell[0]),(1, 1, False, False))))
    return result

def parse_cells(text, count, count2):
    if type(text) is not str:
        raise ValueError("text must be str")
    if len(text) > 2000:
        raise ValueError("text length must be <= 2000")
    
    text = text.strip()
    if not text:
        return checked_cells((),count,count2)
    
    parts = text.split(',')
    cells = []
    for part in parts:
        part = part.strip()
        if not part:
            raise ValueError("Empty entry found")
        
        if ':' not in part:
            raise ValueError(f"Invalid format in '{part}'")
        
        col_str, row_str = part.split(':', 1)
        col_str = col_str.strip()
        row_str = row_str.strip()
        
        if not col_str or not row_str:
            raise ValueError("Empty component found")
        
        if not re.match(r'^[1-9][0-9]{0,2}$', col_str):
            raise ValueError(f"Invalid column format: {col_str}")
        if not re.match(r'^[1-9][0-9]{0,2}$', row_str):
            raise ValueError(f"Invalid row format: {row_str}")
        
        c = int(col_str)
        r = int(row_str)
        
        if c < 1 or r < 1:
            raise ValueError("Coordinates must be >= 1")
        if c > count or r > count2:
            raise ValueError(f"Coordinate ({c}, {r}) out of range")
        
        cells.append((c, r))
    
    return checked_cells(tuple(cells), count, count2)

def format_cells(value, count, count2):
    validated = checked_cells(value, count, count2)
    parts = [f"{c}:{r}" for c, r in validated]
    return ", ".join(parts)
