import math
import html


def values(text, points):
    # Validate text
    if type(text) is not str:
        raise ValueError("text must be a string")
    
    length = len(text)
    if length < 1 or length > 1000:
        raise ValueError("text length must be between 1 and 1000 codepoints")
    
    # Check for invalid characters: C0 controls (0x00-0x1F except LF 0x0A) and DEL (0x7F)
    for char in text:
        code = ord(char)
        if code <= 0x1F and code != 0x0A:
            raise ValueError("text contains invalid C0 control character")
        if code == 0x7F:
            raise ValueError("text contains DEL character")
    
    # Check line count: at most 20 lines split by LF
    # A line is defined by splitting on LF. If there are no LFs, it's 1 line.
    # If there are n LFs, there are n+1 lines.
    line_count = text.count('\n') + 1
    if line_count > 20:
        raise ValueError("text has more than 20 lines")
    
    # Check that there is at least one non-whitespace character
    if not any(not c.isspace() for c in text):
        raise ValueError("text must contain at least one non-whitespace character")
    
    # Validate points
    if type(points) is not tuple:
        raise ValueError("points must be a tuple")
    
    if len(points) != 3:
        raise ValueError("points must have exactly 3 elements")
    
    for i, point in enumerate(points):
        if type(point) is not tuple:
            raise ValueError(f"points[{i}] must be a tuple")
        if len(point) != 2:
            raise ValueError(f"points[{i}] must have exactly 2 coordinates")
        
        x, y = point
        # Check that coordinates are int or float
        if type(x) not in (int,float):
            raise ValueError(f"points[{i}][0] must be int or float")
        if type(y) not in (int,float):
            raise ValueError(f"points[{i}][1] must be int or float")
        
        # Check for NaN/Inf by trying to convert to float and checking
        try:
            fx = float(x)
            fy = float(y)
        except OverflowError:
            raise ValueError(f"points[{i}] contains value causing OverflowError")
        
        if math.isnan(fx) or math.isinf(fx):
            raise ValueError(f"points[{i}][0] must be finite")
        if math.isnan(fy) or math.isinf(fy):
            raise ValueError(f"points[{i}][1] must be finite")
        
        # Check abs <= 1000000
        if abs(fx) > 1000000:
            raise ValueError(f"points[{i}][0] absolute value exceeds 1000000")
        if abs(fy) > 1000000:
            raise ValueError(f"points[{i}][1] absolute value exceeds 1000000")
    
    # Check adjacent segment lengths >= 0.001
    # Points are (arrow tip), (bend), (text end)
    # Segments: (arrow tip) to (bend), (bend) to (text end)
    p0 = (float(points[0][0]), float(points[0][1]))
    p1 = (float(points[1][0]), float(points[1][1]))
    p2 = (float(points[2][0]), float(points[2][1]))
    
    # Segment 0: p0 to p1
    dx0 = p1[0] - p0[0]
    dy0 = p1[1] - p0[1]
    len0 = math.hypot(dx0, dy0)
    if len0 < 0.001:
        raise ValueError("first segment length is less than 0.001")
    
    # Segment 1: p1 to p2
    dx1 = p2[0] - p1[0]
    dy1 = p2[1] - p1[1]
    len1 = math.hypot(dx1, dy1)
    if len1 < 0.001:
        raise ValueError("second segment length is less than 0.001")
    
    # Convert points to tuple of float pairs
    float_points = tuple((float(p[0]), float(p[1])) for p in points)
    
    # Generate HTML string
    escaped_text = html.escape(text, quote=True)
    html_string = '<p>' + escaped_text.replace('\n', '<br/>') + '</p>'
    
    return (text, float_points, html_string)
