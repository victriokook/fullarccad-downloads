"""Conservative straight-edge/planar-face input for native angle chamfer."""
import re
import FreeCAD as App
import Part
from angle_chamfer_values import distance_angle

def checked_input(source,names,distance,angle):
    distance,angle=distance_angle(distance,angle)
    if not source or not hasattr(source,'Shape'):raise ValueError('Select one solid.')
    shape=source.Shape.copy();shape.Placement=App.Placement()
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=1e-9:raise ValueError('Select one valid solid.')
    if shape.ShapeType not in ('Solid','Compound') or (shape.ShapeType=='Compound' and (len(shape.childShapes())!=1 or shape.childShapes()[0].ShapeType!='Solid')):raise ValueError('Extra geometry is not supported.')
    names=list(names)
    if not 1<=len(names)<=200 or len(set(names))!=len(names):raise ValueError('Select distinct edges.')
    for name in names:
        if not isinstance(name,str) or not re.fullmatch(r'Edge[1-9][0-9]*',name) or int(name[4:])>len(shape.Edges):raise ValueError('Invalid edge reference.')
        edge=shape.Edges[int(name[4:])-1]
        try:curve=edge.Curve
        except (TypeError,RuntimeError,Part.OCCError):raise ValueError('Select non-degenerate straight edges.') from None
        if not isinstance(curve,Part.Line) or edge.Length<1e-7:raise ValueError('Select straight edges.')
        faces=[f for f in shape.Faces if any(e.isSame(edge) for e in f.Edges)]
        if len(faces)!=2 or any(not isinstance(f.Surface,Part.Plane) for f in faces):raise ValueError('Each edge must join two planar faces.')
    return shape,names,distance,angle
