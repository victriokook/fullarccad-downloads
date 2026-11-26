"""Restore all trimming to the native finite nonperiodic freeform surface domain."""
import FreeCAD as App
import Part
from surface_isocurve_limits import validate_complexity
from natural_untrim_bounds import checked_bounds
from edge_intersection_bounds import checked_coordinates

def restored(face):
    if face.isNull() or not face.isValid() or face.ShapeType!='Face':raise ValueError('Select one valid face.')
    surface=face.Surface
    if not isinstance(surface,(Part.BSplineSurface,Part.BezierSurface)):raise ValueError('Select a finite BSpline or Bezier surface.')
    validate_complexity(surface.NbUPoles,surface.NbVPoles,surface.UDegree,surface.VDegree)
    if isinstance(surface,Part.BSplineSurface) and (surface.isUPeriodic() or surface.isVPeriodic()):raise ValueError('Periodic surfaces are excluded.')
    for row in surface.getPoles():
        for point in row:checked_coordinates(tuple(point))
    out=surface.toShape();checked_bounds(out.ParameterRange)
    if face.Orientation not in ('Forward','Reversed'):raise ValueError('Unsupported face orientation.')
    if face.Orientation=='Reversed':out.reverse()
    tolerance=max(1e-7,face.Area*1e-9)
    if out.isNull() or not out.isValid() or len(out.Faces)!=1 or out.Solids or len(out.Wires)!=1 or out.Area<=face.Area+tolerance or abs(face.common(out).Area-face.Area)>tolerance:raise ValueError('No recoverable trim or source surface not retained.')
    return out
