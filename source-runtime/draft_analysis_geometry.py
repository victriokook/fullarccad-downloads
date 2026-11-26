"""Signed draft angle at finite-face UV grid samples; not a continuous map."""
import math,re
import FreeCAD as App
import Part,model
from draft_analysis_values import validate
from draft_reference_direction import unit_direction
from surface_isocurve_limits import validate_complexity
from edge_intersection_bounds import checked_coordinates

def reference_direction(doc,reference,name):
    if reference is None or reference.Document!=doc or doc.getObject(reference.Name)!=reference or reference.isDerivedFrom('App::Link'):raise ValueError('Select a reference edge in the current document;links excluded.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [reference]+reference.OutListRecursive):raise ValueError('Repair reference errors first.')
    if type(name) is not str or not re.fullmatch(r'Edge[1-9][0-9]{0,5}',name):raise ValueError('Specify one explicit reference EdgeN.')
    try:edge=model.world_shape(reference).getElement(name)
    except Exception as error:raise ValueError('The reference edge is missing.') from error
    if edge.ShapeType!='Edge' or edge.isNull() or not edge.isValid() or not isinstance(edge.Curve,Part.Line):raise ValueError('Reference must be one straight edge.')
    if not math.isfinite(edge.Length) or not 1e-7<=edge.Length<=1e7:raise ValueError('Reference edge length exceeds supported bounds.')
    for parameter in (edge.FirstParameter,edge.LastParameter):checked_coordinates(tuple(edge.valueAt(parameter)))
    return App.Vector(*unit_direction(*tuple(edge.tangentAt(edge.FirstParameter))))

def samples(doc,source,name,count=15,angle=3.,axis="Z",reverse=False,reference=None,reference_edge="Edge1"):
    use_reference=type(axis) is str and axis=='Reference'
    count,angle,validated_axis,reverse=validate(count,angle,'Z' if use_reference else axis,reverse)
    pull=(reference_direction(doc,reference,reference_edge) if use_reference else App.Vector({"X":(1,0,0),"Y":(0,1,0),"Z":(0,0,1)}[validated_axis]))*(-1 if reverse else 1)
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select one face in the current document;links excluded.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if type(name) is not str or not re.fullmatch(r'Face[1-9][0-9]{0,5}',name):raise ValueError('Select one explicit FaceN.')
    try:face=model.world_shape(source).getElement(name)
    except Exception as error:raise ValueError('The selected face is missing.') from error
    if face.ShapeType!='Face' or face.isNull() or not face.isValid():raise ValueError('Select one valid face.')
    surface=face.Surface
    if not isinstance(surface,(Part.Plane,Part.Cylinder,Part.Cone,Part.Sphere,Part.Toroid,Part.BSplineSurface,Part.BezierSurface)):raise ValueError('Unsupported surface type.')
    if isinstance(surface,(Part.BSplineSurface,Part.BezierSurface)):validate_complexity(surface.NbUPoles,surface.NbVPoles,surface.UDegree,surface.VDegree)
    u1,u2,v1,v2=face.ParameterRange
    if not all(math.isfinite(x) and abs(x)<=1e6 for x in (u1,u2,v1,v2)) or min(u2-u1,v2-v1)<=1e-9:raise ValueError('Unsupported finite UV bounds.')
    values=[]
    for i in range(count):
        for j in range(count):
            u=u1+(u2-u1)*(i+.5)/count;v=v1+(v2-v1)*(j+.5)/count
            if not face.isPartOfDomain(u,v):continue
            point=face.valueAt(u,v);checked_coordinates(tuple(point));normal=face.normalAt(u,v)
            if not all(math.isfinite(x) for x in normal) or normal.Length<1e-9:raise ValueError('The surface normal is undefined.')
            normal.normalize();draft=math.degrees(math.asin(max(-1.,min(1.,normal.dot(pull)))))
            t=max(-1.,min(1.,draft/angle));color=(max(t,0.),1.-abs(t),max(-t,0.))
            values.append(dict(uv=(u,v),point=tuple(point),normal=tuple(normal),draft=draft,color=color))
    if not values:raise ValueError('No UV samples lie on this trimmed face. Increase Samples.')
    return values
