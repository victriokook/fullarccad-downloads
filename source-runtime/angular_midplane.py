"""One deterministic bisector of two nonparallel planar native surfaces."""
import FreeCAD as App
import Part
from angular_midplane_unit import canonical_unit
from edge_intersection_bounds import checked_coordinates

def frame(first,second):
    if not isinstance(first.Surface,Part.Plane) or not isinstance(second.Surface,Part.Plane):raise ValueError('Select planar faces.')
    n1=App.Vector(*canonical_unit(tuple(first.normalAt(0,0))));n2=App.Vector(*canonical_unit(tuple(second.normalAt(0,0))))
    if n1.cross(n2).Length<1e-5:raise ValueError('Use well-separated nonparallel planes.')
    if n1.dot(n2)<0:n2=-n2
    normal=App.Vector(*canonical_unit(tuple(n1+n2)));lines=first.Surface.intersectSS(second.Surface)
    if len(lines)!=1 or not isinstance(lines[0],Part.Line):raise ValueError('Use a unique plane intersection line.')
    x=App.Vector(*canonical_unit(tuple(lines[0].Direction)));point=lines[0].value(0);origin=point-x*point.dot(x);origin=App.Vector(*checked_coordinates(tuple(origin)))
    center=(first.CenterOfMass+second.CenterOfMass)*.5;center-=normal*(center-origin).dot(normal)
    checked_coordinates(tuple(center));rotation=App.Rotation(x,normal.cross(x),normal,'ZXY')
    return App.Placement(origin,rotation),center
