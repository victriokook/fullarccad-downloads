"""Independent indexed native mesh-facet deletion; no automatic filling."""
from collections import Counter
import FreeCAD as App
from i18n import tr
from mesh_delete_values import indices
from model_mesh_components import validate,records
from model_mesh_refine import stamp
from model_mesh_reduce import fingerprint
from model_mesh_merge import valid_geometry

def remove(doc,source,text='1'):
    mesh,pose=validate(doc,source);selected=indices(text,mesh.CountFacets);before=stamp(source);selected_set=set(selected);keep=[i for i in range(mesh.CountFacets) if i not in selected_set]
    expected=mesh.meshFromSegment(keep);removed=mesh.meshFromSegment(list(selected))
    if records(expected)+records(removed)!=records(mesh):raise ValueError('Native extraction changed triangles')
    mesh.removeFacets(list(selected));valid_geometry(mesh)
    if mesh.CountFacets!=len(keep) or records(mesh)!=records(expected):raise ValueError('Native deletion changed retained vertices or orientation')
    if mesh.hasNonManifolds() or mesh.hasSelfIntersections() or mesh.hasNonUniformOrientedFacets():raise ValueError('Invalid result mesh')
    if stamp(source)!=before:raise ValueError('Source changed during deletion')
    return mesh,pose

def create(doc,source,text='1',expected=None):
    import model
    mesh,pose=remove(doc,source,text);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Result differs from preview')
    with model.transaction(doc,tr('メッシュ面を削除','Delete Mesh Faces')):
        out=doc.addObject('Mesh::Feature','DeletedFacesMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('面削除メッシュ','Mesh with Deleted Faces');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
