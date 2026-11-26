import re


def indices(text, count):
    """
    Parse a text string describing facet indices and return a sorted tuple of zero-based indices.
    
    Args:
        text: A string containing comma-separated tokens representing facet indices or ranges.
        count: An integer representing the total number of facets (1-based upper bound).
        
    Returns:
        A sorted tuple of zero-based facet indices.
        
    Raises:
        ValueError: If the input is invalid.
        ValueError: If the input types are incorrect.
    """
    # Validate count type: must be int, not bool
    if type(count) is not int:
        raise ValueError("count must be an integer")
    
    # Validate count range
    if count < 2 or count > 20000:
        raise ValueError("count must be between 2 and 20000")
    
    # Validate text type: must be str
    if type(text) is not str:
        raise ValueError("text must be a string")
    
    # Validate text length
    if len(text) < 1 or len(text) > 4096:
        raise ValueError("text length must be between 1 and 4096")
    
    # Split by comma
    tokens = text.split(',')
    
    # Check for empty tokens
    for token in tokens:
        if token == '':
            raise ValueError("Empty token found")
    
    # Process each token
    all_indices = set()
    total_elements = 0
    
    # Pattern for a single positive integer without leading zeros
    int_pattern = re.compile(r'^[1-9][0-9]*$')
    
    # Pattern for a range: start-end
    range_pattern = re.compile(r'^([1-9][0-9]*)-([1-9][0-9]*)$')
    
    for token in tokens:
        token=token.strip()
        # Try to match as a range
        range_match = range_pattern.fullmatch(token)
        if range_match:
            start_str = range_match.group(1)
            end_str = range_match.group(2)
            start = int(start_str)
            end = int(end_str)
            
            # Check for descending range
            if start<1 or end>count:raise ValueError("Range bounds exceeded")
            if start > end:
                raise ValueError(f"Descending range: {token}")
            
            # Check for duplicate/overlapping entries within the range itself is fine,
            # but we need to check against existing indices later.
            
            # Add range elements
            for i in range(start, end + 1):
                if i in all_indices:
                    raise ValueError(f"Duplicate entry: {i}")
                all_indices.add(i)
                total_elements += 1
                
                # Check out of range
                if i < 1 or i > count:
                    raise ValueError(f"Out of range: {i}")
        else:
            # Try to match as a single integer
            if not int_pattern.fullmatch(token):
                raise ValueError(f"Invalid token: {token}")
            
            val = int(token)
            
            # Check for duplicate
            if val in all_indices:
                raise ValueError(f"Duplicate entry: {val}")
            
            all_indices.add(val)
            total_elements += 1
            
            # Check out of range
            if val < 1 or val > count:
                raise ValueError(f"Out of range: {val}")
    
    # Check for empty selection
    if total_elements == 0:
        raise ValueError("Empty selection")
    
    # Check for all-facets-selected
    if total_elements == count:
        raise ValueError("All facets selected")
    
    # Return sorted tuple of zero-based indices
    return tuple(sorted(i - 1 for i in all_indices))
