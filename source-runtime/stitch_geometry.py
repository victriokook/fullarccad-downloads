"""Exact-boundary stitching candidate; no adjustable tolerance claim."""
import Part
from stitch_limits import validate_face_count

def build(shapes):
    faces=[]
    for shape in shapes:
        if shape.isNull() or not shape.isValid() or shape.ShapeType not in ('Face','Shell'):
            raise ValueError('Select whole valid face or shell objects')
        faces.extend(face.copy() for face in shape.Faces)
    validate_face_count(len(faces))
    result=Part.makeCompound(faces)
    # Installed API accepts a tolerance but does not use it. Expose no such control.
    result.sewShape()
    if result.ShapeType!='Shell' or not result.isValid() or len(result.Faces)!=len(faces):
        raise ValueError('Surfaces must join into one shell without gaps or loose faces')
    tolerance=max(1e-7,sum(f.Area for f in faces)*1e-8)
    if abs(result.Area-sum(f.Area for f in faces))>tolerance:
        raise ValueError('Stitch changed the selected surface area')
    if any(face.common(result).Area<face.Area-max(1e-7,face.Area*1e-7) for face in faces):
        raise ValueError('A selected face was not retained')
    if result.isClosed():
        result=Part.makeSolid(result)
        if not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:
            raise ValueError('Closed shell could not become a valid solid')
    return result
