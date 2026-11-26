def group_rows(records):
    """
    Group records by source_key, validating input and enforcing constraints.
    
    Args:
        records: A list of exactly 1..2000 tuples, each (source_key, source_label, instance_label)
        
    Returns:
        A list of tuples (index, source_key, source_label, count) grouped by source_key,
        preserving first appearance order.
        
    Raises:
        ValueError: If any validation fails.
    """
    if type(records) is not list:
        raise ValueError("records must be a list")
    
    n = len(records)
    if n < 1 or n > 2000:
        raise ValueError("records must contain between 1 and 2000 items")
    
    for i, record in enumerate(records):
        if type(record) is not tuple:
            raise ValueError(f"Record at index {i} must be a tuple")
        if len(record) != 3:
            raise ValueError(f"Record at index {i} must have exactly 3 elements")
        
        source_key, source_label, instance_label = record
        
        
        for j, val in enumerate([source_key, source_label, instance_label]):
            if type(val) is not str:
                raise ValueError(f"Record at index {i}, field {j} must be a str")
            if len(val) == 0:
                raise ValueError(f"Record at index {i}, field {j} must be nonempty")
            if len(val) > 256:
                raise ValueError(f"Record at index {i}, field {j} must be <=256 codepoints")
            for ch in val:
                o = ord(ch)
                if o < 32 or o == 127:
                    raise ValueError(f"Record at index {i}, field {j} contains invalid character with ord {o}")
    
    seen_keys = []  # List of source_keys in order of first appearance
    key_to_source_label = {}  # source_key -> source_label (must be consistent)
    key_to_count = {}  # source_key -> count
    
    for record in records:
        source_key, source_label, instance_label = record
        
        if source_key not in key_to_source_label:
            seen_keys.append(source_key)
            key_to_source_label[source_key] = source_label
            key_to_count[source_key] = 1
        else:
            if key_to_source_label[source_key] != source_label:
                raise ValueError(f"Conflicting source_label for source_key '{source_key}': '{key_to_source_label[source_key]}' vs '{source_label}'")
            key_to_count[source_key] += 1
    
    result = []
    for idx, source_key in enumerate(seen_keys):
        index = idx + 1  # 1-based index
        source_label = key_to_source_label[source_key]
        count = key_to_count[source_key]
        result.append((index, source_key, source_label, count))
    
    return result
