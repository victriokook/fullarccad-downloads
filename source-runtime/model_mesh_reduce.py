"""Independent native mesh decimation;never mutate the source kernel."""
import math,hashlib,struct
import FreeCAD as App
from i18n import tr
from mesh_reduce_values import checked


def fingerprint(mesh):
    points,facets=mesh.Topology;digest=hashlib.sha256()
    for point in points:digest.update(struct.pack('<ddd',point.x,point.y,point.z))
    for facet in facets:digest.update(struct.pack('<III',*facet))
    return digest.hexdigest()


def stamp(source):
    parents=[];current=source.getParentGeoFeatureGroup()
    while current:
        parents.append(current.Name);current=current.getParentGeoFeatureGroup()
    return fingerprint(source.Mesh),str(source.getGlobalPlacement()),tuple(parents),tuple(source.State),str(getattr(source,'Error',''))


def valid_mesh(mesh):
    if not 4<=mesh.CountFacets<=20000:raise ValueError(tr('面数は4～20000に制限しています。','Facet count must be4–20000.'))
    for point in mesh.Topology[0]:
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (point.x,point.y,point.z)):raise ValueError('Mesh coordinates exceed the supported bounds')
    if not mesh.isSolid() or mesh.countComponents()!=1 or mesh.hasNonManifolds() or mesh.hasSelfIntersections():
        raise ValueError(tr('自己交差のない閉じた単一メッシュを指定してください。','Specify one closed,connected mesh without self-intersections.'))
    if not math.isfinite(mesh.Volume) or mesh.Volume<=1e-9:raise ValueError('Mesh must have positive finite volume')


def validate(doc,source):
    if (doc is None or App.ActiveDocument is not doc or source is None or source.Document is not doc or doc.getObject(source.Name) is not source
            or source.TypeId!='Mesh::Feature' or getattr(source,'Error','') or any(s in source.State for s in ('Error','Invalid'))):
        raise ValueError(tr('現在の文書のメッシュを1つ選択してください。','Select one mesh in the active document.'))
    valid_mesh(source.Mesh)
    # Mesh.Topology already includes own placement;use canonical local data and full global pose once.
    mesh=source.Mesh.copy();mesh.Placement=App.Placement();pose=source.getGlobalPlacement()
    for point in mesh.Topology[0]:
        world=pose.multVec(point)
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (world.x,world.y,world.z)):raise ValueError('World mesh coordinates exceed the supported bounds')
    return mesh,pose


def reduce(doc,source,tolerance,reduction):
    tolerance,reduction=checked(tolerance,reduction);mesh,pose=validate(doc,source);before=stamp(source);count=mesh.CountFacets
    mesh.decimate(tolerance,reduction);valid_mesh(mesh)
    if mesh.CountFacets>=count:raise ValueError(tr('この設定では面数が減りません。設定を変更してください。','These settings do not reduce the facet count. Change the settings.'))
    if stamp(source)!=before:raise ValueError('The source changed during decimation')
    return mesh,pose


def create(doc,source,tolerance,reduction,expected=None):
    import model
    mesh,pose=reduce(doc,source,tolerance,reduction);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('The reduction differs from the preview')
    with model.transaction(doc,tr('メッシュ面数を削減','Reduce Mesh Facets')):
        out=doc.addObject('Mesh::Feature','ReducedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('削減メッシュ','Reduced Mesh')
        out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
