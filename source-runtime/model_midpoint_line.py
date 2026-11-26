"""Midpoint-first numeric line creation; standard editable 2D sketch geometry."""
import FreeCAD as App
import Part
from i18n import tr
from midpoint_line_values import endpoints
from conic_geometry import signature

def validate(sketch):
    doc=getattr(sketch,'Document',None)
    if getattr(sketch,'TypeId','')!='Sketcher::SketchObject' or doc is not App.ActiveDocument or doc.getObject(sketch.Name) is not sketch:
        raise ValueError(tr('現在のスケッチを指定してください。','Specify a sketch in the current document.'))
    if any(v in sketch.State for v in ('Invalid','Error')):raise ValueError('Sketch is invalid')
    return doc

def curve(center,length,angle):
    a,b=endpoints(center,length,angle)
    return Part.LineSegment(App.Vector(*a),App.Vector(*b))

def add(sketch,center=(0,0),length=20,angle=0,construction=False):
    import model
    doc=validate(sketch)
    if type(construction) is not bool:raise ValueError('Construction must be boolean')
    geometry=curve(center,length,angle);before=signature(sketch);count=sketch.GeometryCount
    consumers=[(v,len(v.Shape.Solids)) for v in sketch.InListRecursive if hasattr(v,'Shape') and not v.Shape.isNull() and v.Shape.isValid()]
    with model.transaction(doc,tr('中点から線分を追加','Add Midpoint Line')):
        index=sketch.addGeometry(geometry,construction);doc.recompute()
        if index!=count or sketch.solve()!=0:raise ValueError('Sketch cannot be solved')
        after=signature(sketch)
        if after[0][:count]!=before[0] or after[1]!=before[1] or after[2][:count]!=before[2] or after[3]!=before[3]:raise ValueError('Existing sketch geometry changed')
        out=sketch.Geometry[index]
        if not isinstance(out,Part.LineSegment) or (out.StartPoint-geometry.StartPoint).Length>1e-7 or (out.EndPoint-geometry.EndPoint).Length>1e-7 or sketch.getConstruction(index)!=construction:raise ValueError('Created line differs')
        if any(v.Shape.isNull() or not v.Shape.isValid() or any(s in v.State for s in ('Invalid','Error')) or (solids and not v.Shape.Solids) for v,solids in consumers):raise ValueError('Dependent feature failed; addition undone')
    return index
