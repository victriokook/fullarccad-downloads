import math
"""Conservative local geometry validation for native face Draft."""
import FreeCAD as App
import Part
from solid_draft_angle import draft_angle
from draft_side_alignment import check_side_alignment
from cone_draft_radius import check_radius

def checked_input(source,names,neutral,angle):
    angle=draft_angle(angle)
    if not source or not hasattr(source,'Shape'):
        raise ValueError('Select a solid source.')
    shape=source.Shape.copy();shape.Placement=App.Placement()
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=1e-9:
        raise ValueError('Select one valid solid.')
    if shape.ShapeType not in ('Solid','Compound') or (shape.ShapeType=='Compound' and (len(shape.childShapes())!=1 or shape.childShapes()[0].ShapeType!='Solid')):
        raise ValueError('Extra geometry is not supported.')
    names=list(names)
    if not 1<=len(names)<=200 or len(set(names))!=len(names) or neutral in names:
        raise ValueError('Select distinct side faces and a separate neutral face.')
    def face(name,neutral_face=False):
        if not isinstance(name,str) or not name.startswith('Face') or not name[4:].isdigit() or str(int(name[4:]))!=name[4:] or not 1<=int(name[4:])<=len(shape.Faces):
            raise ValueError('Invalid face reference.')
        result=shape.Faces[int(name[4:])-1]
        if neutral_face and not isinstance(result.Surface,Part.Plane):
            raise ValueError('The neutral face must be planar.')
        if not isinstance(result.Surface,(Part.Plane,Part.Cylinder,Part.Cone)):
            raise ValueError('Only planar, cylindrical and complete frustum side faces are supported.')
        return result
    plane=face(neutral,True);normal=plane.Surface.Axis
    for name in names:
        side=face(name)
        kind='cylinder' if isinstance(side.Surface,(Part.Cylinder,Part.Cone)) else 'plane'
        check_side_alignment(kind,side.Surface.Axis.dot(normal))
        if isinstance(side.Surface,Part.Cone):
            circles=[edge.Curve.Radius for edge in side.Edges if isinstance(edge.Curve,Part.Circle)]
            u0,u1,_,_=side.ParameterRange
            if len(side.Edges)!=3 or len(circles)!=2 or abs((u1-u0)-2*math.pi)>1e-7:raise ValueError('Use a complete conical frustum side with two circular ends, not an apex or trimmed sector.')
            reach=max(abs((v.Point-plane.CenterOfMass).dot(normal)) for v in side.Vertexes)
            check_radius(min(circles),reach,angle)
        elif kind=='cylinder':
            reach=max(abs((v.Point-plane.CenterOfMass).dot(normal)) for v in side.Vertexes)
            radius=side.Surface.Radius
            if reach*math.tan(math.radians(angle))>=radius-max(1e-7,radius*1e-9):
                raise ValueError('Cylinder draft radius change must remain smaller than its radius in either direction.')
    return shape,names,neutral,angle
