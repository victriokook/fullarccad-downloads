"""Native arc-length samples and Frenet-normal curvature teeth for one model edge."""
import math,re
import FreeCAD as App
import Part
import model
from edge_comb_values import validate
from edge_intersection_bounds import checked_coordinates

def samples(doc,source,name,count=31,scale=10.,flip=False):
    count,scale,flip=validate(count,scale,flip)
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select one edge in the current document; links excluded.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if type(name) is not str or not re.fullmatch(r'Edge[1-9][0-9]{0,5}',name):raise ValueError('Select one explicit EdgeN.')
    try:edge=model.world_shape(source).getElement(name)
    except Exception as error:raise ValueError('The selected edge is missing.') from error
    if edge.ShapeType!='Edge' or edge.isNull() or not edge.isValid():raise ValueError('Select a valid edge.')
    curve=edge.Curve
    if not isinstance(curve,(Part.Line,Part.Circle,Part.Ellipse,Part.BSplineCurve,Part.BezierCurve)):raise ValueError('Select a line,circle,ellipse,BSpline or Bezier edge.')
    if isinstance(curve,(Part.BSplineCurve,Part.BezierCurve)) and (curve.Degree>9 or curve.NbPoles>200):raise ValueError('Curve complexity exceeds degree9/poles200.')
    length=edge.Length
    if not math.isfinite(length) or not 1e-7<=length<=1e7:raise ValueError('Curve length is outside the supported range.')
    values=[]
    for index in range(count):
        parameter=edge.FirstParameter if index==0 else (edge.LastParameter if index==count-1 else edge.getParameterByLength(length*index/(count-1)))
        if not math.isfinite(parameter):raise ValueError('Invalid curve parameter.')
        point=edge.valueAt(parameter);curvature=float(edge.curvatureAt(parameter));tangent=edge.tangentAt(parameter)
        if not math.isfinite(curvature) or curvature<0 or not all(math.isfinite(v) for v in tangent):raise ValueError('Curvature or tangent is undefined.')
        height=curvature*scale
        if not math.isfinite(height):raise ValueError('Display scale overflows.')
        tip=App.Vector(point)
        if curvature>1e-12:
            normal=edge.normalAt(parameter)
            if not all(math.isfinite(v) for v in normal) or normal.Length<1e-9:raise ValueError('The curve normal is undefined.')
            normal.normalize();tip=point+normal*(height*(-1 if flip else 1))
        checked_coordinates(tuple(point));checked_coordinates(tuple(tip));values.append(dict(parameter=parameter,point=tuple(point),tip=tuple(tip),curvature=curvature))
    return values
