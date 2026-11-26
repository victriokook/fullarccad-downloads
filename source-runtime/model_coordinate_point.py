"""Independent world-coordinate construction points; no linked source/history."""
import FreeCAD as App
import Part
from i18n import tr
from coordinate_point_values import checked,preview_points

def validate(doc):
    if doc is None or App.ActiveDocument is not doc or App.listDocuments().get(doc.Name) is not doc:raise ValueError(tr('現在の文書を開いてください。','Open an active document.'))

def preview(doc,x=0,y=0,z=0):
    validate(doc);xyz=checked(x,y,z);shape=Part.makeCompound([Part.Vertex(App.Vector(*xyz))])
    if shape.isNull() or not shape.isValid() or len(shape.Vertexes)!=1 or shape.Edges or shape.Faces or (shape.Vertexes[0].Point-App.Vector(*xyz)).Length>1e-7:raise ValueError('Native vertex differs from coordinates')
    return shape

def create(doc,x=0,y=0,z=0,expected=None):
    import model
    xyz=checked(x,y,z);shape=preview(doc,*xyz)
    if expected is not None and xyz!=expected:raise ValueError('Coordinates differ from preview')
    with model.transaction(doc,tr('座標で構築点','Construction Point by Coordinates')):
        out=doc.addObject('Part::Feature','CoordinatePoint');out.Shape=shape;out.Label=tr('座標構築点','Coordinate Construction Point');out.ViewObject.PointColor=(.9,.5,.15);out.ViewObject.PointSize=8;doc.recompute()
        if out.OutList or out.getParentGeoFeatureGroup() is not None or out.Shape.Edges or out.Shape.Faces or len(out.Shape.Vertexes)!=1 or (out.Shape.Vertexes[0].Point-App.Vector(*xyz)).Length>1e-7:raise ValueError('Created independent point differs')
    return out
