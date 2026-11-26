def selected_index(names, geometry_count):
    if not isinstance(names, (list, tuple)):
        raise ValueError("names must be a list or tuple")
    if len(names) != 1:
        raise ValueError("names must contain exactly one element")
    
    name = names[0]
    if not isinstance(name, str):
        raise ValueError("name element must be a string")
    
    # Check for forbidden prefixes
    if name.startswith("Vertex"):
        raise ValueError("name cannot start with Vertex")
    if name.startswith("ExternalEdge"):
        raise ValueError("name cannot start with ExternalEdge")
    if name.startswith("Face"):
        raise ValueError("name cannot start with Face")
    
    # Check for Edge prefix and extract suffix
    if not name.startswith("Edge"):
        raise ValueError("name must start with 'Edge'")
    
    suffix = name[4:]  # Remove "Edge" prefix
    
    # Reject suffix length > 5 to avoid huge integer conversion issues
    if len(suffix) > 5:
        raise ValueError("suffix length exceeds limit of 5 characters")
    
    if not suffix.isascii() or not suffix.isdigit():
        raise ValueError("suffix must be ASCII decimal digits")
    
    # Check for leading zeros (canonical positive integer)
    if len(suffix) > 1 and suffix[0] == '0':
        raise ValueError("no leading zeros allowed")
    
    # Convert to integer
    try:
        index = int(suffix)
    except ValueError:
        raise ValueError("suffix must be a valid decimal integer")
    
    # Check for positive integer (canonical positive integer implies > 0)
    if index <= 0:
        raise ValueError("index must be a positive integer")
    
    # Validate geometry_count type and range
    if type(geometry_count) is not int:
        raise ValueError("geometry_count must be an integer")
    if isinstance(geometry_count, bool):
        raise ValueError("geometry_count must be an integer (not bool)")
    if not (1 <= geometry_count <= 10000):
        raise ValueError("geometry_count must be between 1 and 10000")
    
    # Validate index range (1-based input, convert to 0-based output)
    if not (1 <= index <= geometry_count):
        raise ValueError("index must be between 1 and geometry_count")
    
    return index - 1
