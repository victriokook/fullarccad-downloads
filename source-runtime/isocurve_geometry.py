"""Finite supported-face U/V parameter curves clipped by the actual trimmed face."""
import math
import Part
from single_face_input import single_face
from isocurve_values import validate
from isocurve_distribution import positions
from surface_isocurve_limits import validate_complexity

def build(shape,axis,fraction,count=1):
    axis,fraction=validate(axis,fraction);fractions=positions(count,fraction);face=single_face(shape)
    if not isinstance(face.Surface,(Part.Plane,Part.Cylinder,Part.Sphere,Part.Toroid,Part.Cone,Part.BSplineSurface,Part.BezierSurface)):
        raise ValueError('Use a plane, cylinder, sphere, torus, cone, BSpline or Bezier face')
    if isinstance(face.Surface,(Part.BSplineSurface,Part.BezierSurface)):
        surface=face.Surface;validate_complexity(surface.NbUPoles,surface.NbVPoles,surface.UDegree,surface.VDegree)
    u0,u1,v0,v1=face.ParameterRange
    if not all(math.isfinite(v) and abs(v)<=1e6 for v in (u0,u1,v0,v1)) or u1-u0<=1e-12 or v1-v0<=1e-12:
        raise ValueError('Invalid or unbounded face parameter range')
    edges=[]
    for direction in ('U','V') if axis=='UV' else (axis,):
        for fraction in fractions:
            curve=face.Surface.uIso(u0+(u1-u0)*fraction) if direction=='U' else face.Surface.vIso(v0+(v1-v0)*fraction)
            edge=curve.toShape(v0,v1) if direction=='U' else curve.toShape(u0,u1)
            clipped=edge.common(face)
            if clipped.isNull() or not clipped.isValid():raise ValueError('No valid finite isoparametric curve')
            segments=[e for e in clipped.Edges if e.isValid() and e.Length>1e-7]
            if not segments:raise ValueError('Requested parameter curve does not cross the finite face')
            edges.extend(segments)
    if not 1<=len(edges)<=200:raise ValueError('Use a face producing 1..200 curve segments')
    return Part.makeCompound(edges)
