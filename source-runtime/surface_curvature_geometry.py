"""Gaussian curvature at finite-face UV grid samples; not a continuous map."""
import math,re
import FreeCAD as App
import Part,model
from surface_curvature_values import validate
from surface_curvature_metric import value as metric_value
from surface_isocurve_limits import validate_complexity
from edge_intersection_bounds import checked_coordinates

def samples(doc,source,name,count=15,limit=.01,mode="gaussian"):
    count,limit=validate(count,limit);metric_value(0.,0.,mode)
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
            point=face.valueAt(u,v);checked_coordinates(tuple(point));low,high=face.curvatureAt(u,v);gaussian=metric_value(low,high,"gaussian");selected=metric_value(low,high,mode)
            if not all(math.isfinite(x) for x in (low,high,gaussian)):raise ValueError('Curvature is undefined or overflows.')
            # Clamp before division to avoid overflow at a tiny display limit.
            t=max(-1.,min(1.,selected/limit)) if abs(selected)<limit else (1. if selected>0 else -1.)
            color=(max(t,0.),1.-abs(t),max(-t,0.))
            values.append(dict(uv=(u,v),point=tuple(point),gaussian=gaussian,value=selected,mode=mode,color=color))
    if not values:raise ValueError('No UV samples lie on this trimmed face. Increase Samples.')
    return values
