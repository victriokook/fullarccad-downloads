"""Translate one planar boundary edge along an explicit straight-edge direction."""
import math
import FreeCAD as App
import Part,model
from model_construction import element,face
from model_reference_pattern import direction,bounded
from ruled_direction_values import checked_direction_shift
from ruled_direction_element import checked_element
from ruled_ellipse_values import checked_ellipse
from ruled_spline_values import checked_curve

def checked_reference(doc,reference,subelement,existing=None):
    if reference is None or reference.Document!=doc or doc.getObject(reference.Name)!=reference or reference.isDerivedFrom('App::Link') or not hasattr(reference,'Shape'):raise ValueError('Select a current-document straight edge,planar face or construction geometry')
    if existing and (reference==existing or existing in reference.OutListRecursive):raise ValueError('Cyclic direction reference')
    if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [reference]+list(reference.OutListRecursive)):raise ValueError('Repair direction input errors')
    if reference.Shape.isNull() or not reference.Shape.isValid():raise ValueError('Direction source is empty or invalid')
    kind=checked_element(subelement,len(reference.Shape.Edges),len(reference.Shape.Faces))
    if kind=='Edge':return direction(reference,subelement)
    surface=element((reference,subelement),'Face');bounded(surface)
    return face((reference,subelement))[1]

def build(doc,a,b,reference,subelement,distance,angle,reverse,existing=None):
    unit=checked_reference(doc,reference,subelement,existing);curve=element(a,'Edge');surface=element(b,'Face');center,normal=face(b)
    if not isinstance(curve.Curve,(Part.Line,Part.Circle,Part.Ellipse,Part.BSplineCurve,Part.BezierCurve)) or not 1e-7<curve.Length<=1e7:raise ValueError('Use one supported finite planar boundary')
    ellipse=isinstance(curve.Curve,Part.Ellipse)
    spline=isinstance(curve.Curve,(Part.BSplineCurve,Part.BezierCurve))
    if spline:
        basis=curve.Curve;checked_curve(basis.Degree,basis.NbPoles,basis.isPeriodic(),curve.FirstParameter,curve.LastParameter)
        if any(not math.isfinite(v) or abs(v)>1e6 for pole in basis.getPoles() for v in tuple(pole)):raise ValueError('Curve control poles outside finite coordinate limits')
    common_length=__import__('builtins')._fullarc_qt_slot(lambda shape:sum(edge.Length for edge in shape.Edges) if ellipse or spline else shape.Length,(1, 1, False, False))
    if ellipse:checked_ellipse(curve.Curve.MajorRadius,curve.Curve.MinorRadius,curve.FirstParameter,curve.LastParameter)
    if not any(abs(common_length(curve.common(boundary))-curve.Length)<=max(1e-7,curve.Length*1e-9) and abs(boundary.Length-curve.Length)<=max(1e-7,curve.Length*1e-9) for boundary in surface.Edges):raise ValueError('Select a complete boundary of the adjacent planar face')
    if isinstance(curve.Curve,Part.Circle):
        circle=curve.Curve;span=curve.LastParameter-curve.FirstParameter
        if not 1e-6<circle.Radius<=1e6 or not math.isfinite(span) or not 1e-7<span<=2*math.pi+1e-9:raise ValueError('Circle radius or arc span is outside limits')
    shift=App.Vector(*checked_direction_shift(distance,angle,tuple(unit),tuple(normal),reverse));second=curve.copy();second.translate(shift);bounded(curve);bounded(second)
    out=Part.makeRuledSurface(curve,second);bounded(out)
    if out.isNull() or not out.isValid() or len(out.Faces)!=1 or out.Solids or not math.isfinite(out.Area) or out.Area<=1e-9:raise ValueError('Cannot make a valid directional ruled surface')
    for rail in (curve,second):
        if abs(common_length(out.common(rail))-rail.Length)>max(1e-7,rail.Length*1e-8):raise ValueError('Ruled surface does not retain boundary rails')
    if isinstance(curve.Curve,Part.Line):
        expected=curve.Length*shift.cross(curve.tangentAt(curve.FirstParameter)).Length
        if abs(out.Area-expected)>max(1e-7,expected*1e-8):raise ValueError('Ruled surface area differs from the line ruling')
    return out
