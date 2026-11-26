"""Independent native connected-component filtering with exact retained triangles."""
from collections import Counter
import FreeCAD as App
from i18n import tr
from mesh_components_values import checked,partition
from model_mesh_inspect import validate as base_validate
from model_mesh_refine import stamp
from model_mesh_reduce import fingerprint
from model_mesh_merge import valid_geometry

def records(mesh):
    result=Counter()
    for f in mesh.Facets:
        a,b,c=(tuple(p) for p in f.Points);result[min((a,b,c),(b,c,a),(c,a,b))]+=1
    return result

def validate(doc,source):
    mesh=base_validate(doc,source);valid_geometry(mesh)
    if mesh.hasNonManifolds() or mesh.hasSelfIntersections() or mesh.hasNonUniformOrientedFacets():raise ValueError(tr('非多様体・自己交差・法線不整合のないメッシュを指定してください。','Specify a mesh without nonmanifolds, self-intersections or inconsistent orientation.'))
    return mesh,source.getGlobalPlacement()

def remove(doc,source,threshold=1):
    mesh,pose=validate(doc,source);threshold=checked(threshold,mesh.CountFacets);before=stamp(source);components=mesh.getSeparateComponents();counts=[v.CountFacets for v in components];keep,removed=partition(counts,threshold)
    if sum(counts)!=mesh.CountFacets or sum((records(v) for v in components),Counter())!=records(mesh):raise ValueError('Native components changed input triangles')
    expected=sum((records(components[i]) for i in keep),Counter());mesh.removeComponents(threshold);valid_geometry(mesh)
    if mesh.CountFacets!=sum(counts[i] for i in keep) or mesh.countComponents()!=len(keep) or records(mesh)!=expected:raise ValueError('Native component removal changed retained triangles or orientation')
    if mesh.hasNonManifolds() or mesh.hasSelfIntersections() or mesh.hasNonUniformOrientedFacets():raise ValueError('Invalid filtered mesh')
    if stamp(source)!=before:raise ValueError('Source changed during component removal')
    return mesh,pose

def create(doc,source,threshold=1,expected=None):
    import model
    mesh,pose=remove(doc,source,threshold);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Result differs from preview')
    with model.transaction(doc,tr('小さなメッシュ成分を削除','Remove Small Mesh Components')):
        out=doc.addObject('Mesh::Feature','FilteredMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('成分除去メッシュ','Filtered Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
