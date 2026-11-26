"""Non-Boolean mesh merge; preserve internal structures and input orientation."""
import math
import FreeCAD as App
import Mesh
from i18n import tr
from mesh_merge_values import checked_counts
from model_mesh_reduce import fingerprint,stamp as source_stamp

def stamp(sources):return tuple(source_stamp(s) for s in sources)

def valid_geometry(mesh):
    for point in mesh.Topology[0]:
        if any(not math.isfinite(v) or abs(v)>1e6 for v in point):raise ValueError('Mesh coordinates exceed supported bounds')
    if any(not math.isfinite(f.Area) or f.Area<=1e-12 or not .99<f.Normal.Length<1.01 for f in mesh.Facets):raise ValueError('Degenerate mesh facet')

def validate(doc,sources):
    if doc is None or App.ActiveDocument is not doc or type(sources) not in (list,tuple) or not 2<=len(sources)<=20:raise ValueError(tr('現在の文書のメッシュ全体を2～20個選択してください。','Select2–20 whole meshes in the active document.'))
    if len({id(s) for s in sources})!=len(sources):raise ValueError('Duplicate sources')
    for s in sources:
        if s is None or s.Document is not doc or doc.getObject(s.Name) is not s or s.TypeId!='Mesh::Feature' or getattr(s,'Error','') or any(v in s.State for v in ('Error','Invalid')):raise ValueError('Invalid mesh source')
    checked_counts([s.Mesh.CountFacets for s in sources]);items=[]
    for s in sources:
        mesh=s.Mesh.copy();mesh.Placement=App.Placement();valid_geometry(mesh);pose=s.getGlobalPlacement()
        for point in mesh.Topology[0]:
            world=pose.multVec(point)
            if any(not math.isfinite(v) or abs(v)>1e6 for v in world):raise ValueError('World mesh coordinates exceed supported bounds')
        items.append((mesh,pose))
    return items

def merge(doc,sources):
    items=validate(doc,sources);before=stamp(sources);out=Mesh.Mesh();expected=[]
    for mesh,pose in items:
        for f in mesh.Facets:expected.extend(pose.multVec(App.Vector(*v)) for v in f.Points)
        mesh.transform(pose.toMatrix());out.addMesh(mesh)
    if out.CountFacets!=sum(m.CountFacets for m,_ in items):raise ValueError('Native merge changed facet count')
    valid_geometry(out);actual=[App.Vector(*v) for f in out.Facets for v in f.Points]
    for a,e in zip(actual,expected):
        tolerance=max(1e-5,2e-7*max(abs(v) for v in e))
        if (a-e).Length>tolerance:raise ValueError('Native merge changed oriented facet geometry')
    if stamp(sources)!=before:raise ValueError('Sources changed during merge')
    return out,App.Placement()

def create(doc,sources,expected=None):
    import model
    mesh,pose=merge(doc,sources);before=stamp(sources)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Merge differs from preview')
    with model.transaction(doc,tr('メッシュを統合','Merge Meshes')):
        out=doc.addObject('Mesh::Feature','MergedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('統合メッシュ','Merged Mesh');out.ViewObject.ShapeColor=sources[0].ViewObject.ShapeColor;doc.recompute()
        if fingerprint(out.Mesh)!=fingerprint(mesh) or stamp(sources)!=before or out.OutList:raise ValueError('Created mesh differs or sources changed')
        for s in sources:s.Visibility=False
        out.Visibility=True
    return out
