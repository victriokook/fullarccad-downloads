"""Whole-mesh winding reversal with independent output and geometry guards."""
import math
import FreeCAD as App
from i18n import tr
from mesh_reverse_values import sample_indices
from model_mesh_reduce import stamp,fingerprint


def valid_mesh(mesh):
    sample_indices(mesh.CountFacets)
    for point in mesh.Topology[0]:
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (point.x,point.y,point.z)):raise ValueError('Mesh coordinates exceed the supported bounds')
    if mesh.countComponents()!=1 or mesh.hasNonManifolds() or mesh.hasSelfIntersections():raise ValueError(tr('自己交差・非多様体のない単一メッシュを指定してください。','Specify one connected mesh without self-intersections or nonmanifolds.'))
    for facet in mesh.Facets:
        if not math.isfinite(facet.Area) or facet.Area<=1e-12 or not .99<facet.Normal.Length<1.01:raise ValueError('Degenerate mesh facet')


def validate(doc,source):
    if (doc is None or App.ActiveDocument is not doc or source is None or source.Document is not doc or doc.getObject(source.Name) is not source
            or source.TypeId!='Mesh::Feature' or getattr(source,'Error','') or any(s in source.State for s in ('Error','Invalid'))):
        raise ValueError(tr('現在の文書のメッシュを1つ選択してください。','Select one mesh in the active document.'))
    mesh=source.Mesh.copy();mesh.Placement=App.Placement();valid_mesh(mesh);pose=source.getGlobalPlacement()
    for point in mesh.Topology[0]:
        world=pose.multVec(point)
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (world.x,world.y,world.z)):raise ValueError('World mesh coordinates exceed the supported bounds')
    return mesh,pose


def reverse(doc,source):
    mesh,pose=validate(doc,source);before=stamp(source);points,triangles=mesh.Topology;normals=[f.Normal for f in mesh.Facets]
    mesh.flipNormals();valid_mesh(mesh)
    if mesh.Topology[0]!=points or mesh.Topology[1]!=[(a,c,b) for a,b,c in triangles]:raise ValueError('Native reversal changed mesh geometry')
    if any((old+facet.Normal).Length>1e-6 for old,facet in zip(normals,mesh.Facets)):raise ValueError('Native normals did not reverse')
    if stamp(source)!=before:raise ValueError('Source changed during reversal')
    return mesh,pose


def normal_lines(mesh,pose):
    length=max(.001,min(10000,mesh.BoundBox.DiagonalLength*.03));points=[]
    for index in sample_indices(mesh.CountFacets):
        facet=mesh.Facets[index];a,b,c=(App.Vector(*p) for p in facet.Points);center=(a+b+c)/3;normal=facet.Normal;tip=center+normal*length
        side=normal.cross(App.Vector(1,0,0) if abs(normal.x)<.9 else App.Vector(0,1,0));side.normalize()
        left=tip-normal*(length*.25)+side*(length*.12);right=tip-normal*(length*.25)-side*(length*.12)
        points.extend(pose.multVec(p) for p in (center,tip,tip,left,tip,right))
    return points


def create(doc,source,expected=None):
    import model
    mesh,pose=reverse(doc,source);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Reversal differs from preview')
    with model.transaction(doc,tr('メッシュ法線を反転','Reverse Mesh Normals')):
        out=doc.addObject('Mesh::Feature','ReversedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('法線反転メッシュ','Reversed Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
