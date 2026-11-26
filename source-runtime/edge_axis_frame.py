import FreeCAD as App
import Part,math
import model_construction as references

def edge_frame(reference):
    shape=references.element(reference,'Edge')
    if not shape.isValid() or not isinstance(shape.Curve,Part.Line) or shape.Length<1e-7:raise ValueError('Select a valid straight edge')
    first=shape.valueAt(shape.FirstParameter);last=shape.valueAt(shape.LastParameter)
    origin=(first+last)*.5;direction=last-first
    if direction.Length<1e-7 or not all(math.isfinite(v) for v in tuple(origin)+tuple(direction)):raise ValueError('Invalid line axis')
    direction.normalize()
    return origin,direction,App.Vector(origin)
