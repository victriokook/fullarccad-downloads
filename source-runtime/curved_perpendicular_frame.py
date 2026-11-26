import FreeCAD as App
import Part
from curved_perpendicular_values import perpendicular_normal
def frame(reference_a,reference_b,direction='u',offset=0,reversed=False):
    import model_construction as planes
    from model_construction_axis import geometry
    from perpendicular_plane_values import plane_options,checked_point
    from tangent_point_frame import tangent_unit
    direction,offset=plane_options(direction,offset)
    if type(reversed) is not bool:raise ValueError('Expected boolean Flip Normal')
    shape=planes.element(reference_a,'Face')
    if not shape.isValid() or not isinstance(shape.Surface,(Part.Cylinder,Part.Cone,Part.Toroid)):raise ValueError('Use cylinder,cone or torus')
    point,normal,_=geometry('normal_point',reference_a=reference_a,reference_b=reference_b,reversed=False)
    checked_point(tuple(point));u,v=shape.Surface.parameter(point);first,second=shape.tangentAt(u,v)
    along=App.Vector(*tangent_unit(tuple(first if direction=='u' else second),tuple(normal)))
    newnormal=App.Vector(*perpendicular_normal(tuple(along),tuple(normal),reversed))
    origin=App.Vector(*checked_point(tuple(point+newnormal*offset)))
    return App.Placement(origin,App.Rotation(along,newnormal.cross(along),newnormal,'ZXY')),origin
