"""Ordered planar/linear reference comparison within native linear tolerance."""
import FreeCAD as App
from unstitch_stamp import shape_fingerprint

def reference_matches(current,saved):
    if shape_fingerprint(current)==shape_fingerprint(saved):return True
    a=current.copy();b=saved.copy();a.Placement=App.Placement();b.Placement=App.Placement()
    if a.ShapeType!=b.ShapeType or a.Orientation!=b.Orientation:return False
    if any(len(getattr(a,key))!=len(getattr(b,key)) for key in ('Vertexes','Edges','Wires','Faces','Shells','Solids')):return False
    tolerance=1e-7
    if any((x.Point-y.Point).Length>tolerance for x,y in zip(a.Vertexes,b.Vertexes)):return False
    for x,y in zip(a.Edges,b.Edges):
        if x.Orientation!=y.Orientation or len(x.Vertexes)!=len(y.Vertexes) or type(x.Curve)!=type(y.Curve):return False
        if abs(x.Length-y.Length)>tolerance or abs(x.common(y).Length-x.Length)>tolerance:return False
        if any((u.Point-v.Point).Length>tolerance for u,v in zip(x.Vertexes,y.Vertexes)):return False
    for x,y in zip(a.Faces,b.Faces):
        if x.Orientation!=y.Orientation or type(x.Surface)!=type(y.Surface) or len(x.Wires)!=len(y.Wires):return False
        area_tolerance=max(1e-7,x.Area*1e-9)
        if abs(x.Area-y.Area)>area_tolerance or abs(x.common(y).Area-x.Area)>area_tolerance:return False
        if any(len(u.Edges)!=len(v.Edges) for u,v in zip(x.Wires,y.Wires)):return False
    return True
