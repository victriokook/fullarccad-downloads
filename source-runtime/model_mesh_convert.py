"""Independent faceted mesh to CAD conversion with strict triangle matching."""
import hashlib,math
import FreeCAD as App
import Part
from i18n import tr
from mesh_convert_values import checked_facets
from model_mesh_reverse import validate as base_validate,stamp

def triangle_key(points):return tuple(sorted(tuple(0.0 if v==0 else v for v in p) for p in points))

def fingerprint(shape):
    records=sorted((triangle_key(v.Point for v in f.Vertexes),tuple(round(v,9) or 0.0 for v in f.normalAt(0,0))) for f in shape.Faces)
    return hashlib.sha256(repr((shape.ShapeType,records)).encode()).hexdigest()

def matches(actual,expected):
    if actual.ShapeType!=expected.ShapeType or len(actual.Faces)!=len(expected.Faces):return False
    for a,e in zip(actual.Faces,expected.Faces):
        if (a.CenterOfMass-e.CenterOfMass).Length>1e-7 or (a.normalAt(0,0)-e.normalAt(0,0)).Length>1e-7:return False
        remaining=[v.Point for v in e.Vertexes]
        for vertex in a.Vertexes:
            found=next((i for i,p in enumerate(remaining) if (vertex.Point-p).Length<=1e-7),None)
            if found is None:return False
            remaining.pop(found)
        if remaining:return False
    return True

def validate(doc,source):
    if source is not None and source.TypeId=='Mesh::Feature':checked_facets(source.Mesh.CountFacets)
    mesh,pose=base_validate(doc,source);checked_facets(mesh.CountFacets)
    if mesh.hasNonUniformOrientedFacets():raise ValueError(tr('先にメッシュ法線を整合してください。','Harmonize mesh normals first.'))
    return mesh,pose

def convert(doc,source):
    mesh,pose=validate(doc,source);before=stamp(source);shape=Part.Shape();shape.makeShapeFromMesh(mesh.Topology,1e-7)
    if mesh.isSolid():shape=Part.makeSolid(shape)
    if shape.isNull() or not shape.isValid() or len(shape.Faces)!=mesh.CountFacets or shape.ShapeType not in ('Face','Shell','Solid'):raise ValueError('Native conversion did not produce a valid faceted shape')
    if mesh.isSolid():
        if len(shape.Solids)!=1 or not math.isfinite(shape.Volume) or shape.Volume<=1e-9:raise ValueError(tr('閉メッシュの向きを外向きにして再試行してください。','Orient the closed mesh outward and try again.'))
        points,facets=mesh.Topology;origin=points[0]
        reference=math.fsum((points[a]-origin).dot((points[b]-origin).cross(points[c]-origin))/6 for a,b,c in facets)
        if not math.isfinite(reference) or reference<=1e-9 or abs(shape.Volume-reference)>max(1e-6,reference*1e-7):raise ValueError('Converted volume differs from independent triangle integration')
    elif shape.Solids:raise ValueError('An open mesh unexpectedly became solid')
    expected={triangle_key(f.Points):f.Normal for f in mesh.Facets}
    actual={triangle_key(v.Point for v in f.Vertexes):f.normalAt(0,0) for f in shape.Faces}
    if len(expected)!=mesh.CountFacets or len(actual)!=len(expected) or actual.keys()!=expected.keys() or any((actual[k]-expected[k]).Length>1e-6 for k in expected):raise ValueError('Converted triangles or normals differ')
    points,facets=mesh.Topology
    reference_area=math.fsum((points[b]-points[a]).cross(points[c]-points[a]).Length/2 for a,b,c in facets)
    if abs(shape.Area-reference_area)>max(1e-6,reference_area*1e-7):raise ValueError('Converted area differs from independent triangle integration')
    if stamp(source)!=before:raise ValueError('Source changed during conversion')
    return shape,pose

def preview_data(shape):return shape.tessellate(.1)

def create(doc,source,expected=None):
    import model
    shape,pose=convert(doc,source);before=stamp(source)
    if expected is not None and fingerprint(shape)!=expected:raise ValueError('Conversion differs from preview')
    with model.transaction(doc,tr('メッシュをCAD形状へ変換','Convert Mesh to CAD')):
        out=doc.addObject('Part::Feature','ConvertedMesh');out.Shape=shape;out.Placement=pose;out.Label=tr('変換CAD形状','Converted CAD Shape');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Shape.copy();actual.Placement=App.Placement()
        if not matches(actual,shape) or stamp(source)!=before or out.OutList:raise ValueError('Created shape differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
