"""Independent finite reference plane from world centre and normal; no links."""
import math
import FreeCAD as App
import Part
from i18n import tr
from model_coordinate_point import validate
from coordinate_plane_values import checked,corners

def matches(shape,origin,normal,size):
    o,n,length=checked(origin,normal,size);points=corners(origin,normal,size)
    if shape.isNull() or not shape.isValid() or shape.ShapeType!='Face' or len(shape.Faces)!=1 or len(shape.Edges)!=4 or len(shape.Vertexes)!=4 or not isinstance(shape.Surface,Part.Plane):return False
    if not math.isfinite(shape.Area) or abs(shape.Area-length*length)>max(1e-8,length*length*1e-9) or (shape.CenterOfMass-App.Vector(*o)).Length>1e-6:return False
    if shape.normalAt(0,0).dot(App.Vector(*n))<1-1e-8:return False
    return all(min((vertex.Point-App.Vector(*point)).Length for vertex in shape.Vertexes)<=1e-7 for point in points[:4])

def preview(doc,origin=(0,0,0),normal=(0,0,1),size=80):
    validate(doc);points=corners(origin,normal,size)
    try:shape=Part.Face(Part.makePolygon([App.Vector(*point) for point in points]))
    except Exception as error:raise ValueError('Native plane cannot be built: '+str(error)) from error
    if not matches(shape,origin,normal,size):raise ValueError('Native plane differs from requested frame')
    return shape

def create(doc,origin=(0,0,0),normal=(0,0,1),size=80,expected=None):
    import model
    points=corners(origin,normal,size);shape=preview(doc,origin,normal,size)
    if expected is not None and points!=expected:raise ValueError('Plane differs from preview')
    with model.transaction(doc,tr('座標と法線で平面を作成','Create Plane by Coordinates and Normal')):
        out=doc.addObject('Part::Feature','CoordinatePlane');out.Shape=shape;out.Label=tr('座標平面','Coordinate Plane');out.ViewObject.ShapeColor=(.96,.68,.28);out.ViewObject.LineColor=(.72,.44,.14);out.ViewObject.Transparency=75;doc.recompute()
        if out.OutList or out.getParentGeoFeatureGroup() is not None or not matches(out.Shape,origin,normal,size):raise ValueError('Created independent plane differs')
    return out
