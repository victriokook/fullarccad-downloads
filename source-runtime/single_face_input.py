"""Strict whole-face input adapter for one-face compound wrappers only."""

def single_face(shape):
    if shape.isNull() or not shape.isValid():raise ValueError("A valid whole face is required")
    current=shape
    for depth in range(9):
        if current.ShapeType=='Face':
            if len(current.Faces)!=1 or current.Solids:raise ValueError("Exactly one face is required")
            return current.copy()
        if current.ShapeType!='Compound':raise ValueError("Select a face or a one-face compound")
        children=current.childShapes()
        if len(children)!=1:raise ValueError("Loose geometry or multiple faces are not supported")
        current=children[0]
    raise ValueError("Nested compound depth exceeds eight")
