"""Independent world-coordinate line used as a construction axis."""
import FreeCAD as App
import Part
from i18n import tr
from coordinate_axis_values import checked,endpoints
from model_coordinate_point import validate

def preview(doc,origin=(0,0,0),direction=(0,0,1),length=80):
    validate(doc);a,b=endpoints(origin,direction,length);shape=Part.makeCompound([Part.makeLine(App.Vector(*a),App.Vector(*b))])
    edge=shape.Edges[0]
    if not shape.isValid() or shape.Faces or len(shape.Edges)!=1 or len(shape.Vertexes)!=2 or (edge.Vertexes[0].Point-App.Vector(*a)).Length>1e-7 or (edge.Vertexes[-1].Point-App.Vector(*b)).Length>1e-7:raise ValueError('Native line differs from coordinates')
    return shape

def create(doc,origin=(0,0,0),direction=(0,0,1),length=80,expected=None):
    import model
    ends=endpoints(origin,direction,length);shape=preview(doc,origin,direction,length)
    if expected is not None and ends!=expected:raise ValueError('Axis differs from preview')
    with model.transaction(doc,tr('座標と方向で構築軸','Construction Axis by Coordinates')):
        out=doc.addObject('Part::Feature','CoordinateAxis');out.Shape=shape;out.Label=tr('座標構築軸','Coordinate Construction Axis');out.ViewObject.LineColor=(.9,.5,.15);out.ViewObject.LineWidth=3;out.ViewObject.PointSize=5;doc.recompute()
        if out.OutList or out.getParentGeoFeatureGroup() is not None or len(out.Shape.Edges)!=1 or any((v.Point-App.Vector(*end)).Length>1e-7 for v,end in zip(out.Shape.Vertexes,ends)):raise ValueError('Created independent axis differs')
    return out
