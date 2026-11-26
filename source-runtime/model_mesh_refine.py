"""Independent guarded native mesh refinement."""
import math
import FreeCAD as App
from i18n import tr
from mesh_refine_values import checked
from model_mesh_reduce import fingerprint
from model_mesh_reverse import validate as base_validate,valid_mesh

def stamp(source):
    parents=[];current=source.getParentGeoFeatureGroup()
    while current:
        parents.append((current.Name,str(current.Placement),tuple(s for s in current.State if s in ('Error','Invalid')),str(getattr(current,'Error',''))));current=current.getParentGeoFeatureGroup()
    return fingerprint(source.Mesh),str(source.getGlobalPlacement()),tuple(parents),tuple(s for s in source.State if s in ('Error','Invalid')),str(getattr(source,'Error',''))

def validate(doc,source):
    mesh,pose=base_validate(doc,source)
    if not mesh.isSolid() or mesh.hasNonUniformOrientedFacets() or not math.isfinite(mesh.Volume) or mesh.Volume<=1e-9:raise ValueError(tr('向きが整合した閉じた単一メッシュを指定してください。','Specify one closed mesh with consistent orientation.'))
    parent=source.getParentGeoFeatureGroup()
    while parent:
        if getattr(parent,'Error','') or any(s in parent.State for s in ('Error','Invalid')):raise ValueError('Invalid source container')
        parent=parent.getParentGeoFeatureGroup()
    return mesh,pose

def refine(doc,source,iterations=1):
    mesh,pose=validate(doc,source);iterations,upper=checked(iterations,mesh.CountFacets);before=stamp(source);original=mesh.CountFacets
    for _ in range(iterations):
        mesh.refine();valid_mesh(mesh)
        if not mesh.isSolid() or mesh.hasNonUniformOrientedFacets() or not math.isfinite(mesh.Volume) or mesh.Volume<=1e-9:raise ValueError('Refinement produced an invalid closed mesh')
    if mesh.CountFacets<=original or mesh.CountFacets>upper:raise ValueError(tr('面数が増えませんでした。別の入力または回数を指定してください。','Facet count did not increase. Choose another mesh or pass count.'))
    for point in mesh.Topology[0]:
        world=pose.multVec(point)
        if any(not math.isfinite(v) or abs(v)>1e6 for v in world):raise ValueError('Refined world bounds exceeded')
    if stamp(source)!=before:raise ValueError('Source changed during refinement')
    return mesh,pose

def create(doc,source,iterations=1,expected=None):
    import model
    mesh,pose=refine(doc,source,iterations);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Refinement differs from preview')
    with model.transaction(doc,tr('メッシュを細分化','Refine Mesh')):
        out=doc.addObject('Mesh::Feature','RefinedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('細分化メッシュ','Refined Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
