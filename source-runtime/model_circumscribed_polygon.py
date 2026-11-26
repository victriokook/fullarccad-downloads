"""Apothem-first regular polygon using FreeCAD native ProfileLib constraints."""
import math
import FreeCAD as App
import Part
from i18n import tr
from circumscribed_polygon_values import vertices
from model_midpoint_line import validate,signature

def outline(center,sides,apothem,angle):return Part.makePolygon([App.Vector(*p) for p in vertices(center,sides,apothem,angle)])

def add(sketch,center=(0,0),sides=6,apothem=10,angle=0,construction=False):
    import model
    from ProfileLib.RegularPolygon import makeRegularPolygon
    doc=validate(sketch)
    if type(construction) is not bool:raise ValueError('Construction must be boolean')
    points=vertices(center,sides,apothem,angle);before=signature(sketch);count=sketch.GeometryCount;constraints=sketch.ConstraintCount
    consumers=[(v,len(v.Shape.Solids)) for v in sketch.InListRecursive if hasattr(v,'Shape') and not v.Shape.isNull() and v.Shape.isValid()]
    with model.transaction(doc,tr('外接ポリゴンを追加','Add Circumscribed Polygon')):
        makeRegularPolygon(sketch,sides,App.Vector(center[0],center[1],0),App.Vector(*points[0]),construction);doc.recompute()
        if sketch.GeometryCount!=count+sides+1 or sketch.ConstraintCount!=constraints+3*sides-1 or sketch.solve()!=0:raise ValueError('Native polygon could not be solved')
        after=signature(sketch)
        if after[0][:count]!=before[0] or after[1][:constraints]!=before[1] or after[2][:count]!=before[2] or after[3]!=before[3]:raise ValueError('Existing sketch changed')
        for i in range(sides):
            line=sketch.Geometry[count+i]
            if not isinstance(line,Part.LineSegment) or (line.StartPoint-App.Vector(*points[i])).Length>1e-7 or (line.EndPoint-App.Vector(*points[i+1])).Length>1e-7 or sketch.getConstruction(count+i)!=construction:raise ValueError('Native polygon differs')
        circle=sketch.Geometry[count+sides]
        if not isinstance(circle,Part.Circle) or not sketch.getConstruction(count+sides) or (circle.Center-App.Vector(center[0],center[1],0)).Length>1e-7 or abs(circle.Radius-float(apothem)/math.cos(math.pi/sides))>1e-7:raise ValueError('Native construction circle differs')
        if any(v.Shape.isNull() or not v.Shape.isValid() or any(s in v.State for s in ('Invalid','Error')) or (solids and not v.Shape.Solids) for v,solids in consumers):raise ValueError('Dependent feature failed; polygon undone')
    return count
