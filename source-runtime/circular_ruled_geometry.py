"""Native ruled face between a planar circular boundary and concentric offset rail."""
import math
import FreeCAD as App
import Part
from circular_ruled_radius import checked_radius
from edge_intersection_bounds import checked_coordinates

def build(edge,face,distance,angle,mode,reverse):
    if not isinstance(edge.Curve,Part.Circle) or not isinstance(face.Surface,Part.Plane):raise ValueError('Select a circular boundary and adjacent planar face.')
    if not any(abs(edge.common(boundary).Length-edge.Length)<=max(1e-7,edge.Length*1e-9) and abs(boundary.Length-edge.Length)<=max(1e-7,edge.Length*1e-9) for boundary in face.Edges):raise ValueError('Select a complete boundary edge of the planar face.')
    circle=edge.Curve;normal=face.normalAt(0,0);normal.normalize();alignment=normal.dot(circle.Axis)
    if abs(alignment)<1-1e-7:raise ValueError('Circle and planar face must be coplanar.')
    span=edge.LastParameter-edge.FirstParameter
    if not math.isfinite(span) or span<=1e-7 or span>2*math.pi+1e-9:raise ValueError('Select a finite nondegenerate circle or arc.')
    sign=-1. if reverse else 1.;theta=math.radians(angle)
    axial=sign*distance*(math.cos(theta) if mode=='normal' else math.sin(theta))
    radial=-math.copysign(1.,alignment)*sign*distance*(math.sin(theta) if mode=='normal' else math.cos(theta))
    radius=checked_radius(circle.Radius,radial);second=circle.copy();second.Radius=radius;second.Center=circle.Center+normal*axial
    # Conservative complete-circle bounds also cover every selected arc and every ruling.
    for rail in (circle,second):
        extents=[rail.Radius*math.sqrt(max(0.,1.-component*component)) for component in rail.Axis]
        checked_coordinates(tuple(center+extent for center,extent in zip(rail.Center,extents)));checked_coordinates(tuple(center-extent for center,extent in zip(rail.Center,extents)))
    rail=second.toShape(edge.FirstParameter,edge.LastParameter);out=Part.makeRuledSurface(edge,rail)
    expected=span*(circle.Radius+radius)*distance*.5
    if out.isNull() or not out.isValid() or len(out.Faces)!=1 or out.Solids or abs(out.Area-expected)>max(1e-7,expected*1e-8):raise ValueError('Cannot make a valid circular ruled surface.')
    if abs(out.common(edge).Length-edge.Length)>max(1e-7,edge.Length*1e-8) or abs(out.common(rail).Length-rail.Length)>max(1e-7,rail.Length*1e-8):raise ValueError('Ruled surface does not retain its boundary rails.')
    return out
