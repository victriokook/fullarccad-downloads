import unicodedata

def checked_text(text):
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    
    stripped = text.strip()
    if not stripped:
        raise ValueError("Text cannot be empty after stripping whitespace.")
    
    if len(text) > 100:
        raise ValueError("Text length exceeds maximum of 100 characters.")
    
    allowed_ranges = [(32,126),(0x3000,0x303F),(0x3041,0x3096),(0x309D,0x309F),
                      (0x30A0,0x30FF),(0x31F0,0x31FF),(0x3400,0x4DBF),
                      (0x4E00,0x9FFF),(0xFF01,0xFF9F)]

    for char in text:
        code = ord(char)
        
        if not ((32 <= code <= 126) or any(start <= code <= end for start, end in allowed_ranges)):
            raise ValueError("Character is not allowed.")
        
        category = unicodedata.category(char)
        if category.startswith('M') or category.startswith('C'):
            raise ValueError("Combining or control characters are not allowed.")
    
    return text
