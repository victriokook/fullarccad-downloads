"""Native elliptic arcs in the active sketch,with transactional append guards."""
import math
import FreeCAD as App
import Part
from i18n import tr
from elliptical_arc_values import checked
from conic_geometry import signature


def curve(cx,cy,major,minor,rotation,start,sweep):
    cx,cy,major,minor,rotation,start,sweep=checked(cx,cy,major,minor,rotation,start,sweep)
    center=App.Vector(cx,cy,0);angle=math.radians(rotation)
    u=App.Vector(math.cos(angle),math.sin(angle),0);v=App.Vector(-math.sin(angle),math.cos(angle),0)
    ellipse=Part.Ellipse(center+u*major,center+v*minor,center)
    return Part.ArcOfEllipse(ellipse,math.radians(start),math.radians(start+sweep))


def add(sketch,cx,cy,major,minor,rotation,start,sweep,construction=False):
    import model
    if (getattr(sketch,'TypeId','')!='Sketcher::SketchObject' or sketch.Document is not App.ActiveDocument
            or sketch.Document.getObject(sketch.Name) is not sketch or getattr(sketch,'Error','')
            or any(state in sketch.State for state in ('Error','Invalid'))):
        raise ValueError(tr('有効な現在のスケッチを指定してください。','Specify a valid sketch in the active document.'))
    if type(construction) is not bool:raise ValueError('Construction must be boolean')
    geometry=curve(cx,cy,major,minor,rotation,start,sweep);doc=sketch.Document;before=signature(sketch);count=sketch.GeometryCount
    dependents={obj.Name:(bool(obj.Shape.Solids),bool(obj.Shape.Faces),bool(obj.Shape.Edges)) for obj in sketch.InListRecursive
                if hasattr(obj,'Shape') and not obj.Shape.isNull() and obj.Shape.isValid()}
    with model.transaction(doc,tr('楕円弧を追加','Add Elliptical Arc')):
        index=sketch.addGeometry(geometry,construction);doc.recompute()
        if index!=count or sketch.solve()!=0:raise ValueError(tr('スケッチを解けません。追加を取り消しました。','Cannot solve the sketch;addition was undone.'))
        after=signature(sketch)
        if after[0][:count]!=before[0] or after[1]!=before[1] or after[2][:count]!=before[2] or after[3]!=before[3]:
            raise ValueError(tr('既存の図形が変わりました。追加を取り消しました。','Existing geometry changed;addition was undone.'))
        actual=sketch.Geometry[index]
        if actual.TypeId!='Part::GeomArcOfEllipse' or sketch.getConstruction(index)!=construction:
            raise ValueError('Native arc conversion changed the geometry type')
        for k in range(33):
            parameter=geometry.FirstParameter+(geometry.LastParameter-geometry.FirstParameter)*k/32
            if (geometry.value(parameter)-actual.value(parameter)).Length>1e-7:raise ValueError('Native arc geometry differs')
        for name,old in dependents.items():
            child=doc.getObject(name);shape=getattr(child,'Shape',None)
            if (child is None or getattr(child,'Error','') or any(state in child.State for state in ('Error','Invalid'))
                    or shape is None or shape.isNull() or not shape.isValid()
                    or any(was and not now for was,now in zip(old,(bool(shape.Solids),bool(shape.Faces),bool(shape.Edges))))):
                raise ValueError(tr('後の加工を更新できません。追加を取り消しました。','A dependent feature cannot update;addition was undone.'))
    return index
