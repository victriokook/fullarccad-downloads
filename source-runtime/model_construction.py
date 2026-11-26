from tangent_offset_values import checked_distance,resolve_distance
"""Linked construction planes from planar/round faces, axes and vertices."""
import math
import re
import FreeCAD as App
import Part
import model
from offset_point_distance import signed_offset
from tangent_point_frame import tangent_unit
from two_edge_plane_guard import validate_pair
import perpendicular_plane_values
import tangent_reference_values
import model_path_pattern
import path_plane_object_values
from path_plane_extension_values import extended_station
from i18n import tr


def title(kind):
    if kind=='perpendicular_point':return tr('頂点を通る垂直平面','Perpendicular Plane Through Vertex')
    if kind=='offset_point':return tr('頂点を通る平行平面','Offset Plane Through Vertex')
    if kind=='tangent_point':return tr('面上の頂点での接平面','Tangent Plane at Vertex on Face')
    if kind=='two_edges':return tr('2辺を通る平面','Plane Through Two Edges')
    if kind=='along_path':return tr('パスに沿った平面','Plane Along Path')
    if kind=='tangent':return tr('接平面','Tangent Plane')
    if kind=='three_points':return tr('3点を通る平面','Plane Through Three Points')
    if kind=='offset':return tr('オフセット平面','Offset Plane')
    return tr('中間平面','Midplane') if kind in ('midplane','two_edges','tangent_point','offset_point','perpendicular_point') else tr('角度付き平面','Plane at Angle')


def resolve(doc,name,subname):
    obj=doc.getObject(name)
    if obj is None:raise ValueError(tr('参照がありません。','The reference is missing.'))
    if subname:
        obj=obj.getSubObject(subname,1) or obj
        subname=subname.rsplit('.',1)[-1]
    elif getattr(obj,'FluxPlane',False):subname='Face1'
    elif hasattr(obj,'Shape') and obj.Shape.ShapeType=='Vertex':subname='Vertex1'
    return obj,subname


def element(ref,kind):
    if not ref or ref[0] is None:raise ValueError(tr('参照を選択してください。','Select a reference.'))
    obj,sub=ref
    if (not re.fullmatch(kind+r'[1-9]\d*',sub or '') or not hasattr(obj,'Shape') or
            'Invalid' in obj.State or getattr(obj,'Error','')):
        if kind=='Vertex':raise ValueError(tr('頂点またはスケッチの端点を選択してください。','Select a vertex or sketch endpoint.'))
        raise ValueError(tr('平らな面を選択してください。','Select a planar face.') if kind=='Face' else
                         tr('直線の辺を選択してください。','Select a straight edge.'))
    try:return model.world_shape(obj).getElement(sub)
    except Exception:raise ValueError(tr('参照先の要素がありません。選び直してください。','The referenced element is missing. Select it again.'))


def face(ref):
    shape=element(ref,'Face')
    if not isinstance(shape.Surface,Part.Plane):raise ValueError(tr('曲面ではなく平らな面を選択してください。','Select a planar face, not a curved surface.'))
    normal=shape.normalAt(0,0);normal.normalize()
    return shape.CenterOfMass,normal


def edge(ref):
    shape=element(ref,'Edge')
    if not isinstance(shape.Curve,Part.Line) or shape.Length<1e-7:
        raise ValueError(tr('回転軸には直線の辺を選択してください。','Select a straight edge for the rotation axis.'))
    first,last=shape.valueAt(shape.FirstParameter),shape.valueAt(shape.LastParameter)
    direction=last-first;direction.normalize()
    return (first+last)*.5,direction


def vertex(ref):
    point=element(ref,'Vertex').Point
    if not all(math.isfinite(v) for v in point):raise ValueError(tr('有効な頂点を選択してください。','Select a valid vertex.'))
    return point


def points_frame(reference_a,reference_b,reference_c,reversed=False):
    first,second,third=[vertex(ref) for ref in (reference_a,reference_b,reference_c)]
    x=second-first;v=third-first;length=max(x.Length,v.Length,(third-second).Length)
    if min(x.Length,v.Length,(third-second).Length)<1e-7:
        raise ValueError(tr('位置の異なる3つの点を選択してください。','Select three points at different positions.'))
    normal=x.cross(v)
    if normal.Length/length<max(1e-6,length*1e-10):
        raise ValueError(tr('3点が一直線上、または一直線に近すぎます。別の点を選択してください。',
                            'The three points are collinear or too close to a straight line. Select another point.'))
    x.normalize();normal.normalize()
    if reversed:normal=-normal
    rotation=App.Rotation(x,normal.cross(x),normal,'ZXY')
    return App.Placement(first,rotation),(first+second+third)/3


def edges_frame(reference_a,reference_b,offset=0,reversed=False):
    first,d1=edge(reference_a);second,d2=edge(reference_b);cross=d1.cross(d2)
    validate_pair(cross.Length,0)
    normal=App.Vector(cross);normal.normalize();validate_pair(cross.Length,abs((second-first).dot(normal)))
    origin=first+d1*((second-first).cross(d2).dot(cross)/cross.dot(cross))
    if reversed:normal=-normal
    rotation=App.Rotation(d1,normal.cross(d1),normal,'ZXY')
    origin+=normal*offset;center=(first+second)*.5+normal*offset
    return App.Placement(origin,rotation),center


def tangent_point_frame(reference_a,reference_b,angle=0,reversed=False):
    from model_construction_axis import geometry
    origin,normal,_=geometry('normal_point',reference_a=reference_a,reference_b=reference_b,reversed=reversed)
    shape=element(reference_a,'Face');u,v=shape.Surface.parameter(origin);first,second=shape.tangentAt(u,v)
    x=App.Vector(*tangent_unit(tuple(first),tuple(normal)))
    rotation=App.Rotation(x,normal.cross(x),normal,'ZXY');rotation=App.Rotation(normal,angle).multiply(rotation)
    return App.Placement(origin,rotation),App.Vector(origin)


def perpendicular_point_frame(reference_a,reference_b,direction='u',offset=0,reversed=False):
    direction,offset=perpendicular_plane_values.plane_options(direction,offset)
    if type(reversed) is not bool:raise ValueError('Expected boolean Flip Normal')
    for ref in (reference_a,reference_b):
        if ref and ref[0] and ref[0].isDerivedFrom('App::Link'):raise ValueError('Links are excluded')
    shape=element(reference_a,'Face')
    if isinstance(shape.Surface,(Part.Cylinder,Part.Cone,Part.Toroid)):
        from curved_perpendicular_frame import frame
        return frame(reference_a,reference_b,direction,offset,reversed)
    if not isinstance(shape.Surface,Part.Plane) or not shape.isValid():raise ValueError('Select a valid planar FaceN')
    point=App.Vector(*perpendicular_plane_values.checked_point(tuple(vertex(reference_b))))
    u,v=shape.Surface.parameter(point);first,second=shape.tangentAt(u,v);normal=shape.normalAt(u,v)
    along=App.Vector(*tangent_unit(tuple(first if direction=='u' else second),tuple(normal)))
    normal=along.cross(normal);normal.normalize()
    if reversed:normal=-normal
    origin=App.Vector(*perpendicular_plane_values.checked_point(tuple(point+normal*offset)))
    return App.Placement(origin,App.Rotation(along,normal.cross(along),normal,'ZXY')),origin


def offset_point_frame(reference_a,reference_b,reversed=False):
    frame,center,normal=offset_frame('face',reference_a);point=vertex(reference_b)
    distance=signed_offset(normal.dot(point-frame.Base));origin=frame.Base+normal*distance
    if reversed:
        normal=-normal;x=frame.Rotation.multVec(App.Vector(1,0,0));rotation=App.Rotation(x,normal.cross(x),normal,'ZXY')
    else:rotation=frame.Rotation
    return App.Placement(origin,rotation),point


def round_face(ref):
    if ref and not re.fullmatch(r'Face[1-9]\d*',ref[1] or ''):
        raise ValueError(tr('円柱または円すいの側面を選択してください。','Select a cylindrical or conical side face.'))
    shape=element(ref,'Face')
    if not isinstance(shape.Surface,(Part.Cylinder,Part.Cone)):
        raise ValueError(tr('円柱または円すいの側面を選択してください。','Select a cylindrical or conical side face.'))
    if not shape.isValid() or not all(math.isfinite(v) for v in shape.ParameterRange):
        raise ValueError(tr('有限で有効な曲面を選択してください。','Select a valid, bounded curved face.'))
    return shape


def tangent_angle(ref,point=None):
    """Use the picked point when available, otherwise choose a valid angular start."""
    shape=round_face(ref);u0,u1,v0,v1=shape.ParameterRange
    u=0 if u1-u0>=2*math.pi-1e-7 else (u0+u1)*.5
    if point is not None:
        picked=App.Vector(*point)
        if (all(math.isfinite(v) for v in picked) and
                shape.distToShape(Part.Vertex(picked))[0]<=max(1e-5,shape.BoundBox.DiagonalLength*.002)):
            u=shape.Surface.parameter(picked)[0]
    return (math.degrees(u)+180)%360-180


def _tangent_frame_base(reference_a,angle=0,reversed=False):
    shape=round_face(reference_a);surface=shape.Surface
    u0,u1,v0,v1=shape.ParameterRange
    u=math.radians(angle);u+=math.ceil((u0-u-1e-9)/(2*math.pi))*2*math.pi
    if u>u1+1e-9:
        raise ValueError(tr('この角度に選択した曲面がありません。角度を変更してください。','The selected face does not cover this angle. Choose another angle.'))
    u=max(u0,min(u1,u));v=(v0+v1)*.5;contact=surface.value(u,v)
    if not shape.isInside(contact,1e-6,True):
        # A cutout may occupy the middle. Find a remaining segment on this generator.
        section=shape.common(Part.makeLine(surface.value(u,v0),surface.value(u,v1)))
        edges=[e for e in section.Edges if e.Length>1e-7]
        if not edges:
            raise ValueError(tr('この角度に選択した曲面がありません。角度を変更してください。','The selected face does not cover this angle. Choose another angle.'))
        contact=max(edges,key=__import__('builtins')._fullarc_qt_slot(lambda e:e.Length,(1, 1, False, False))).CenterOfMass;v=surface.parameter(contact)[1]
    origin=surface.value(u,0);generator=surface.value(u,1)-origin
    normal=shape.normalAt(u,v);normal.normalize();x=generator.cross(normal)
    if x.Length<1e-9:raise ValueError(tr('この位置では接平面を定義できません。','A tangent plane cannot be defined at this location.'))
    x.normalize()
    if reversed:normal=-normal
    rotation=App.Rotation(x,normal.cross(x),normal,'ZXY')
    # V=0 is independent of trimming and height, including a cone's apex.
    return App.Placement(origin,rotation),contact


def tangent_frame(reference_a,angle=0,reversed=False,reference_b=None,tangent_reference=False):
    if tangent_reference is None:tangent_reference=False
    if type(tangent_reference) is not bool:raise ValueError('Expected boolean reference mode')
    if not tangent_reference:return _tangent_frame_base(reference_a,angle,reversed)
    for ref in (reference_a,reference_b):
        if ref and ref[0] and ref[0].isDerivedFrom('App::Link'):raise ValueError('Links are excluded')
    shape=round_face(reference_a);surface=shape.Surface
    if isinstance(surface,Part.Cone):
        from cone_reference_radius import checked_radius
        u0,u1,v0,v1=shape.ParameterRange
        midpoint=surface.value((u0+u1)*.5,(v0+v1)*.5)
        radius=checked_radius((midpoint-surface.Center).cross(surface.Axis).Length)
        probe_center=surface.Center+surface.Axis*((midpoint-surface.Center).dot(surface.Axis))
    elif isinstance(surface,Part.Cylinder):
        if not 1e-7<surface.Radius<=1e6:raise ValueError('Cylinder radius outside reference-mode limits')
        radius=surface.Radius
        probe_center=surface.Center
    else:raise ValueError('Reference mode requires a cylindrical or conical FaceN')
    _,normal=face(reference_b)
    tangent_reference_values.validate_incidence(normal.dot(surface.Axis))
    if any(not math.isfinite(v) or abs(v)>1e6 for v in tuple(surface.Center)):raise ValueError('Cylinder center outside world limits')
    parameter=surface.parameter(probe_center+normal*radius)[0]
    absolute=tangent_reference_values.angle_from_reference(parameter,angle)
    frame,contact=_tangent_frame_base(reference_a,absolute,reversed)
    if any(not math.isfinite(v) or abs(v)>1e6 for point in (frame.Base,contact) for v in tuple(point)):raise ValueError('Reference tangent coordinates outside world limits')
    return frame,contact


def path_curve(ref):
    if not ref or ref[0] is None:raise ValueError(tr('経路を選択してください。','Select a path.'))
    if ref[1] and not re.fullmatch(r'Edge[1-9]\d*',ref[1]):
        raise ValueError(tr('辺、またはつながった経路のスケッチを選択してください。','Select an edge or a sketch with one connected path.'))
    wire=Part.Wire([element(ref,'Edge')]) if ref[1] else None
    try:
        curve=model_path_pattern.Path(ref[0],wire)
        if not curve.wire.isValid() or not math.isfinite(curve.length) or curve.length<1e-7:raise ValueError('Invalid path')
        return curve
    except Exception as error:
        raise ValueError(tr('有効な辺、または枝分かれのない1本の経路を選択してください。','Select a valid edge or a single connected path without branches.')) from error


def _path_frame_base(reference_a,path_mode='fraction',fraction=.5,path_distance=10,path_reverse=False,angle=0,reversed=False):
    if path_mode not in ('fraction','distance') or not math.isfinite(fraction) or not 0<=fraction<=1:
        raise ValueError(tr('位置の比率は0～100%で指定してください。','Enter a position from 0 to 100%.'))
    if not math.isfinite(path_distance) or not 0<=path_distance<=1000000:
        raise ValueError(tr('経路上の距離は0～1000000 mmで指定してください。','Enter a path distance from 0 to 1000000 mm.'))
    curve=path_curve(reference_a);distance=curve.length*fraction if path_mode=='fraction' else path_distance
    if distance>curve.length+max(1e-7,curve.length*1e-9):
        raise ValueError(tr('指定した距離が経路の長さを超えています。','The distance exceeds the path length.'))
    distance=min(distance,curve.length)
    # At a sharp corner there is no single perpendicular plane. Require a side.
    station=curve.length-distance if path_reverse else distance
    tolerance=max(1e-7,curve.length*1e-9)
    boundaries=list(zip(curve.ends[:-1],curve.edges[:-1],curve.edges[1:]))
    if curve.closed:boundaries.extend((s,curve.edges[-1],curve.edges[0]) for s in (0,curve.length))
    for boundary,before,after in boundaries:
        if abs(station-boundary)<=tolerance:
            a=before.tangentAt(before.FirstParameter if before.Orientation=='Reversed' else before.LastParameter)*(-1 if before.Orientation=='Reversed' else 1)
            b=after.tangentAt(after.LastParameter if after.Orientation=='Reversed' else after.FirstParameter)*(-1 if after.Orientation=='Reversed' else 1)
            if a.dot(b)<1-1e-8:
                raise ValueError(tr('経路の角では方向が定まりません。位置を角の前後へずらしてください。','A sharp corner has no unique normal plane. Move the position before or after the corner.'))
    origin,normal=curve.at(distance,path_reverse);_,initial=curve.at(0,path_reverse)
    source=reference_a[0].getGlobalPlacement().Rotation
    # Seed from object-local axes so a rigid source rotation carries the frame.
    local=source.inverted().multVec(initial)
    x=source.multVec(App.Vector(1,0,0) if abs(local.x)<.9 else App.Vector(0,1,0));x-=initial*x.dot(initial);x.normalize()
    transport=model_path_pattern.placements(curve,[distance],'tangent',path_reverse,x)[0].Rotation
    x=transport.multVec(x);x-=normal*x.dot(normal);x.normalize()
    x=App.Rotation(normal,angle).multVec(x)
    if reversed:normal=-normal
    rotation=App.Rotation(x,normal.cross(x),normal,'ZXY')
    return App.Placement(origin,rotation),curve,distance




def path_object_frame(reference_a,reference_b,path_reverse=False,angle=0,reversed=False,path_object_offset=None):
    edge_shape=element(reference_a,'Edge');point=vertex(reference_b)
    if not isinstance(edge_shape.Curve,Part.Line) or not 1e-7<edge_shape.Length<=1e7:
        raise ValueError('To Object requires one straight EdgeN')
    if any(not math.isfinite(v) or abs(v)>1e6 for vector in [point]+[v.Point for v in edge_shape.Vertexes] for v in tuple(vector)):
        raise ValueError('Reference coordinates exceed +/-1000000mm')
    offset=path_plane_object_values.checked_offset(0 if path_object_offset is None else path_object_offset)
    parameter=edge_shape.Curve.parameter(point)
    distance=path_plane_object_values.station(parameter,edge_shape.FirstParameter,edge_shape.LastParameter,edge_shape.Orientation=='Reversed',bool(path_reverse),offset)
    frame,curve,_=_path_frame_base(reference_a,'distance',.5,0,path_reverse,angle,reversed)
    origin,direction=curve.at(0,path_reverse);frame.Base=origin+direction*distance
    if any(not math.isfinite(v) or abs(v)>1e6 for v in tuple(frame.Base)):
        raise ValueError('To Object plane origin exceeds +/-1000000mm')
    return frame,curve,distance


def path_frame(reference_a,path_mode='fraction',fraction=.5,path_distance=10,path_reverse=False,angle=0,reversed=False,path_extend=None,reference_b=None,path_object_offset=None):
    if path_extend is None:path_extend=False
    if type(path_extend) is not bool:raise ValueError('Path extension must be a boolean')
    if path_mode=='to_object':return path_object_frame(reference_a,reference_b,path_reverse,angle,reversed,path_object_offset)
    if not path_extend or path_mode!='distance':
        return _path_frame_base(reference_a,path_mode,fraction,path_distance,path_reverse,angle,reversed)
    curve=path_curve(reference_a)
    if len(curve.edges)>200:raise ValueError('Extended path requires at most200 edges')
    station,extension=extended_station(path_distance,curve.length,bool(curve.closed))
    frame,curve,_=_path_frame_base(reference_a,path_mode,fraction,station,path_reverse,angle,reversed)
    if extension:
        _,direction=curve.at(station,path_reverse)
        frame.Base=frame.Base+direction*extension
        if any(not math.isfinite(value) or abs(value)>1e6 for value in tuple(frame.Base)):
            raise ValueError('Extended plane origin exceeds +/-1000000mm')
    return frame,curve,float(path_distance)


def references(kind,reference_a=None,reference_b=None,reference_c=None,base='XY',axis='X',axis_reference=None,**unused):
    if kind=='along_path':return [reference_a,reference_b] if unused.get('path_mode')=='to_object' else [reference_a]
    if kind=='tangent':return [reference_a,reference_b] if unused.get('tangent_reference',False) else [reference_a]
    if kind=='three_points':return [reference_a,reference_b,reference_c]
    return [reference_a,reference_b] if kind in ('midplane','two_edges','tangent_point','offset_point','perpendicular_point') else ([reference_a] if base=='face' else [])+([axis_reference] if kind=='angle' and axis=='edge' else [])


def offset_frame(base='XY',reference_a=None):
    """Anchor a face frame to its object, independent of the finite face bounds."""
    normals={'XY':App.Vector(0,0,1),'XZ':App.Vector(0,1,0),'YZ':App.Vector(1,0,0)}
    if base=='face':
        center,normal=face(reference_a)
        source=reference_a[0].getGlobalPlacement()
        origin=source.Base+normal*normal.dot(center-source.Base)
        rotation=source.Rotation.multiply(App.Rotation(App.Vector(0,0,1),source.Rotation.inverted().multVec(normal)))
    elif base in normals:
        center=origin=App.Vector();normal=normals[base]
        rotation=App.Rotation(App.Vector(0,0,1),normal)
    else:raise ValueError(tr('基準平面を選択してください。','Select a reference plane.'))
    return App.Placement(origin,rotation),center,normal


def check_sources(doc,kind,existing=None,**values):
    if existing and (existing.Document!=doc or getattr(existing,'FluxConstructionPlane','')!=kind):
        raise ValueError(tr('同じ種類の構築平面を選んでください。','Select a construction plane of the same type.'))
    for ref in references(kind,**values):
        if not ref or ref[0] is None:raise ValueError(tr('参照を選択してください。','Select a reference.'))
        obj=ref[0]
        if obj.Document!=doc:raise ValueError(tr('同じ文書内の参照を選んでください。','Select references in the same document.'))
        if existing and (obj==existing or existing in obj.OutListRecursive):
            raise ValueError(tr('この平面自身や後続の加工は参照できません。','Cannot reference this plane or its descendants.'))


def build(kind,reference_a=None,reference_b=None,reference_c=None,base='XY',axis='X',axis_reference=None,angle=45,size=80,offset=10,reversed=False,path_mode='fraction',fraction=.5,path_distance=10,path_reverse=False,tangent_offset=None,path_extend=None,path_object_offset=None,perpendicular_direction=None,perpendicular_offset=None,tangent_reference=None):
    if kind not in ('midplane','angle','offset','three_points','tangent','along_path','two_edges','tangent_point','offset_point','perpendicular_point'):raise ValueError('Unknown plane type')
    if not math.isfinite(size) or not .1<=size<=1000000:
        raise ValueError(tr('表示サイズは0.1～1000000 mmで指定してください。','Enter a display size from 0.1 to 1000000 mm.'))
    if not math.isfinite(angle) or not -180<=angle<=180:
        raise ValueError(tr('角度は−180～180度で指定してください。','Enter an angle from -180 to 180 degrees.'))
    if not math.isfinite(offset) or not -1000000<=offset<=1000000:
        raise ValueError(tr('距離は−1000000～1000000 mmで指定してください。','Enter a distance from -1000000 to 1000000 mm.'))
    if kind=='perpendicular_point':
        frame,center=perpendicular_point_frame(reference_a,reference_b,'u' if perpendicular_direction is None else perpendicular_direction,0 if perpendicular_offset is None else perpendicular_offset,reversed);origin=frame.Base;rotation=frame.Rotation
    elif kind=='offset_point':
        frame,center=offset_point_frame(reference_a,reference_b,reversed);origin=frame.Base;rotation=frame.Rotation
    elif kind=='tangent_point':
        frame,center=tangent_point_frame(reference_a,reference_b,angle,reversed);origin=frame.Base;rotation=frame.Rotation
    elif kind=='two_edges':
        frame,center=edges_frame(reference_a,reference_b,offset,reversed);origin=frame.Base;rotation=frame.Rotation
    elif kind=='along_path':
        frame,curve,distance=path_frame(reference_a,path_mode,fraction,path_distance,path_reverse,angle,reversed,path_extend,reference_b,path_object_offset)
        origin=center=frame.Base;rotation=frame.Rotation
    elif kind=='tangent':
        frame,center=tangent_frame(reference_a,angle,reversed,reference_b,tangent_reference)
        tangent_offset=resolve_distance(tangent_offset)
        normal=frame.Rotation.multVec(App.Vector(0,0,1))
        origin=frame.Base;rotation=frame.Rotation
        if tangent_offset:
            origin=origin+normal*tangent_offset;center=center+normal*tangent_offset
            if any(not math.isfinite(x) or abs(x)>1e6 for point in (origin,center) for x in tuple(point)):
                raise ValueError('Offset tangent plane coordinates exceed +/-1000000mm.')
    elif kind=='three_points':
        frame,center=points_frame(reference_a,reference_b,reference_c,reversed)
        origin=frame.Base;rotation=frame.Rotation
    elif kind=='offset':
        frame,center,normal=offset_frame(base,reference_a)
        origin=frame.Base+normal*offset;rotation=frame.Rotation;center+=normal*offset
    elif kind=='midplane':
        first,normal=face(reference_a);second,other=face(reference_b)
        if reference_a==reference_b:raise ValueError(tr('異なる2つの面を選択してください。','Select two different faces.'))
        if abs(normal.dot(other))<1-1e-10:
            from angular_midplane import frame
            midframe,center=frame(element(reference_a,'Face'),element(reference_b,'Face'));origin=midframe.Base;rotation=midframe.Rotation
        else:
            origin=normal*((normal.dot(first)+normal.dot(second))*.5)
            rotation=App.Rotation(App.Vector(0,0,1),normal);center=(first+second)*.5
    else:
        normals={'XY':App.Vector(0,0,1),'XZ':App.Vector(0,1,0),'YZ':App.Vector(1,0,0)}
        if base=='face':point,normal=face(reference_a)
        elif base in normals:point,normal=App.Vector(),normals[base]
        else:raise ValueError(tr('基準平面を選択してください。','Select a reference plane.'))
        if axis=='edge':center,direction=edge(axis_reference)
        elif axis in ('X','Y','Z'):center,direction=App.Vector(),normals[{'X':'YZ','Y':'XZ','Z':'XY'}[axis]]
        else:raise ValueError(tr('回転軸を選択してください。','Select a rotation axis.'))
        if abs(normal.dot(direction))>1e-7 or abs(normal.dot(center-point))>1e-6:
            raise ValueError(tr('軸が基準平面上にありません。面上の直線辺、または面内の軸を選んでください。',
                                'The axis must lie in the reference plane. Select an in-plane straight edge or axis.'))
        # Project the global origin to the axis: edge length edits cannot move the sketch origin.
        origin=center-direction*direction.dot(center)
        rotation=App.Rotation(direction,angle).multiply(App.Rotation(direction,normal.cross(direction),normal,'ZXY'))
    pose=App.Placement(origin,rotation)
    local=pose.inverse().multVec(center);half=size*.5
    # Keep the surface origin at local zero; trimming only controls the visible patch.
    shape=Part.Plane().toShape(local.x-half,local.x+half,local.y-half,local.y+half)
    shape.Placement=pose
    if not shape.isValid():raise ValueError(tr('平面を作成できません。','Cannot create this plane.'))
    return shape


def unpack(link):
    return (link[0],link[1][0] if link[1] else '') if link and link[0] else None


def settings(obj):
    values=dict(reference_a=unpack(obj.ReferenceA),reference_b=unpack(obj.ReferenceB),base=str(obj.BasePlane),
                axis=str(obj.Axis),axis_reference=unpack(obj.AxisReference),angle=obj.Angle.Value,size=obj.Size.Value)
    # Existing midplane/angle files predate the offset property.
    if obj.FluxConstructionPlane in ('offset','two_edges'):values['offset']=obj.Offset.Value
    if obj.FluxConstructionPlane=='two_edges':values['reversed']=obj.Reversed
    if obj.FluxConstructionPlane=='three_points':values.update(reference_c=unpack(obj.ReferenceC),reversed=obj.Reversed)
    if obj.FluxConstructionPlane in ('tangent','tangent_point','offset_point','perpendicular_point'):values['reversed']=obj.Reversed
    if obj.FluxConstructionPlane=='tangent':values.update(tangent_offset=float(getattr(obj,'TangentOffset',0)),tangent_reference=bool(getattr(obj,'TangentReference',False)))
    if obj.FluxConstructionPlane=='perpendicular_point':values.update(perpendicular_direction=str(obj.PerpendicularDirection),perpendicular_offset=obj.PerpendicularOffset.Value)
    if obj.FluxConstructionPlane=='along_path':values.update(path_mode=str(obj.PathMode),fraction=obj.Fraction,path_distance=obj.PathDistance.Value,path_reverse=obj.PathReverse,reversed=obj.Reversed,path_extend=bool(getattr(obj,'PathExtend',False)),path_object_offset=float(getattr(obj,'PathObjectOffset',0)))
    return values


class ConstructionPlane:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        try:
            shape=build(str(obj.FluxConstructionPlane),**settings(obj))
            # Convert the computed world frame if the plane is later put inside a component.
            parent=obj.getGlobalPlacement().multiply(obj.Placement.inverse())
            pose=parent.inverse().multiply(shape.Placement)
            shape.Placement=App.Placement();obj.Shape=shape;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def create(doc,kind,existing=None,**values):
    if kind=='tangent':values['tangent_offset']=resolve_distance(values.get('tangent_offset'),float(getattr(existing,'TangentOffset',0)) if existing else 0)
    if kind=='along_path' and values.get('path_extend') is None:values['path_extend']=bool(getattr(existing,'PathExtend',False)) if existing else False
    if kind=='along_path':values['path_object_offset']=path_plane_object_values.checked_offset(values.get('path_object_offset') if values.get('path_object_offset') is not None else float(getattr(existing,'PathObjectOffset',0)) if existing else 0)
    if kind=='perpendicular_point':
        direction=values.get('perpendicular_direction');distance=values.get('perpendicular_offset')
        values['perpendicular_direction'],values['perpendicular_offset']=perpendicular_plane_values.plane_options(str(existing.PerpendicularDirection) if direction is None and existing else 'u' if direction is None else direction,existing.PerpendicularOffset.Value if distance is None and existing else 0 if distance is None else distance)
    if kind=='tangent' and values.get('tangent_reference') is None:values['tangent_reference']=bool(getattr(existing,'TangentReference',False)) if existing else False
    check_sources(doc,kind,existing,**values);expected=build(kind,**values)
    if unchanged(existing,kind,**values):return existing
    solid_dependents={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,title(kind)):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython',{'midplane':'Midplane','angle':'AngledPlane','offset':'OffsetPlane','three_points':'ThreePointPlane','tangent':'TangentPlane','along_path':'PathPlane','two_edges':'TwoEdgePlane','tangent_point':'TangentPointPlane','offset_point':'OffsetPointPlane','perpendicular_point':'PerpendicularPointPlane'}[kind]);obj.Label=title(kind)
            for typ,key in [('App::PropertyBool','FluxPlane'),('App::PropertyString','FluxConstructionPlane'),
                            ('App::PropertyLinkSubGlobal','ReferenceA'),('App::PropertyLinkSubGlobal','ReferenceB'),
                            ('App::PropertyLinkSubGlobal','AxisReference'),('App::PropertyLinkListGlobal','SourceContainers'),
                            ('App::PropertyEnumeration','BasePlane'),('App::PropertyEnumeration','Axis'),
                            ('App::PropertyAngle','Angle'),('App::PropertyLength','Size'),('App::PropertyString','Error')]:
                obj.addProperty(typ,key,'Construction')
            obj.FluxPlane=True;obj.FluxConstructionPlane=kind;obj.BasePlane=['XY','XZ','YZ','face'];obj.Axis=['X','Y','Z','edge']
            for key in ('FluxPlane','FluxConstructionPlane','ReferenceA','ReferenceB','AxisReference','SourceContainers'):obj.setEditorMode(key,2)
            for key in ('Placement','BasePlane','Axis','Error'):obj.setEditorMode(key,1)
            if kind in ('offset','two_edges'):obj.addProperty('App::PropertyDistance','Offset','Construction')
            if kind=='three_points':
                obj.addProperty('App::PropertyLinkSubGlobal','ReferenceC','Construction');obj.setEditorMode('ReferenceC',2)
            if kind in ('three_points','tangent','along_path','two_edges','tangent_point','offset_point','perpendicular_point'):
                obj.addProperty('App::PropertyBool','Reversed','Construction')
            if kind=='along_path':
                for typ,key in [('App::PropertyEnumeration','PathMode'),('App::PropertyFloat','Fraction'),('App::PropertyLength','PathDistance'),('App::PropertyBool','PathReverse')]:obj.addProperty(typ,key,'Construction')
                obj.PathMode=['fraction','distance']
            ConstructionPlane(obj);obj.ViewObject.Proxy=0
        if kind=='perpendicular_point':
            if 'PerpendicularDirection' not in obj.PropertiesList:
                obj.addProperty('App::PropertyEnumeration','PerpendicularDirection','Construction');obj.PerpendicularDirection=['u','v']
                obj.addProperty('App::PropertyDistance','PerpendicularOffset','Construction')
            obj.PerpendicularDirection=values['perpendicular_direction'];obj.PerpendicularOffset=values['perpendicular_offset']
        if kind=='tangent':
            if 'TangentReference' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','TangentReference','Construction')
            obj.TangentReference=values['tangent_reference']
            if 'TangentOffset' not in obj.PropertiesList:obj.addProperty('App::PropertyDistance','TangentOffset','Construction')
            obj.TangentOffset=values['tangent_offset']
        data=dict(reference_a=None,reference_b=None,reference_c=None,base='XY',axis='X',axis_reference=None,angle=45,size=80,offset=10,reversed=False,path_mode='fraction',fraction=.5,path_distance=10,path_reverse=False,tangent_offset=0.,path_extend=False,path_object_offset=0.,tangent_reference=False);data.update(values)
        # Irrelevant references must not remain as hidden dependencies after changing modes.
        if kind in ('angle','offset'):
            data['reference_b']=None
            if data['base']!='face':data['reference_a']=None
            if kind=='offset' or data['axis']!='edge':data['axis_reference']=None
        else:data['axis_reference']=None
        if kind=='tangent':
            if not data['tangent_reference']:data['reference_b']=None
            data['base']='face'
        if kind=='along_path' and data['path_mode']!='to_object':data['reference_b']=None
        for prop,key in [('ReferenceA','reference_a'),('ReferenceB','reference_b'),('AxisReference','axis_reference')]:
            ref=data[key];setattr(obj,prop,(ref[0],[ref[1]]) if ref else None)
        if kind=='three_points':
            ref=data['reference_c'];obj.ReferenceC=(ref[0],[ref[1]])
        if kind in ('three_points','tangent','along_path','two_edges','tangent_point','offset_point','perpendicular_point'):obj.Reversed=bool(data['reversed'])
        if kind=='along_path':
            if 'PathExtend' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','PathExtend','Construction')
            obj.PathExtend=data['path_extend']
            if 'PathObjectOffset' not in obj.PropertiesList:obj.addProperty('App::PropertyDistance','PathObjectOffset','Construction')
            obj.PathObjectOffset=data['path_object_offset']
            previous_mode=str(obj.PathMode);obj.PathMode=['fraction','distance','to_object'];obj.PathMode=previous_mode
            obj.PathMode=data['path_mode'];obj.Fraction=data['fraction'];obj.PathDistance=data['path_distance'];obj.PathReverse=bool(data['path_reverse'])
        parents=[]
        for ref in references(kind,**data):
            parent=ref[0].getParentGeoFeatureGroup()
            while parent:
                if obj in parent.OutListRecursive:raise ValueError(tr('平面を含むグループは参照できません。','Cannot reference a group containing this plane.'))
                if parent not in parents:parents.append(parent)
                parent=parent.getParentGeoFeatureGroup()
        obj.SourceContainers=parents;obj.BasePlane=data['base'];obj.Axis=data['axis'];obj.Angle=data['angle'];obj.Size=data['size']
        if kind in ('offset','two_edges'):obj.Offset=data['offset']
        doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        if obj.Shape.isNull() or not obj.Shape.isValid() or abs(obj.Shape.Area-expected.Area)>1e-6:
            raise ValueError(tr('平面を作成できません。','Cannot create this plane.'))
        for dependent in obj.InListRecursive:
            if ('Invalid' in dependent.State or getattr(dependent,'Error','') or
                (hasattr(dependent,'Shape') and ((dependent.Shape.isNull() and dependent.TypeId!='Sketcher::SketchObject') or
                  (not dependent.Shape.isNull() and not dependent.Shape.isValid()) or (dependent.Name in solid_dependents and not dependent.Shape.Solids)))):
                raise ValueError(tr('後続の加工が成立しないため変更を取り消しました。','The edit would invalidate a later feature and was cancelled.'))
        if not existing:
            obj.ViewObject.ShapeColor=(.96,.68,.28);obj.ViewObject.LineColor=(.72,.44,.14);obj.ViewObject.Transparency=75
    return obj


def unchanged(existing, kind, **values):
    if existing is None or existing.FluxConstructionPlane != kind or existing.Error or existing.Shape.isNull() or not existing.Shape.isValid():
        return False
    data = dict(reference_a=None, reference_b=None, reference_c=None, base='XY', axis='X', axis_reference=None, angle=45, size=80, offset=10, reversed=False, path_mode='fraction', fraction=.5, path_distance=10, path_reverse=False, tangent_offset=0., tangent_reference=False)
    data.update(values)
    if kind in ('angle', 'offset'):
        data['reference_b'] = None
        if data['base'] != 'face':
            data['reference_a'] = None
        if kind == 'offset' or data['axis'] != 'edge':
            data['axis_reference'] = None
    else:
        data['axis_reference'] = None
    if kind == 'tangent':
        if not data['tangent_reference']:data['reference_b'] = None
        data['base'] = 'face'
    if kind == 'along_path' and data['path_mode'] != 'to_object':
        data['reference_b'] = None
    return all(value == data[key] for key, value in settings(existing).items())
