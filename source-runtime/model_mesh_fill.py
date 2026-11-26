"""Conservative whole-mesh hole filling; independent closed output only."""
import math
import FreeCAD as App
from i18n import tr
from mesh_fill_values import checked_count
from model_mesh_reverse import validate as base_validate,valid_mesh,stamp,fingerprint

def boundaries(mesh):
    edges={}
    for a,b,c in mesh.Topology[1]:
        for x,y in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((x,y)));edges[key]=edges.get(key,0)+1
    boundary=[e for e,n in edges.items() if n==1]
    if len(boundary)>200:raise ValueError('Total boundary edges exceed200')
    graph={}
    for a,b in boundary:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    if any(len(v)!=2 for v in graph.values()):raise ValueError('Boundary is not a set of simple loops')
    visited=set();loops=[]
    for start in graph:
        if start in visited:continue
        pending=[start];count=0
        while pending:
            point=pending.pop()
            if point in visited:continue
            visited.add(point);count+=1;pending.extend(graph[point]-visited)
        loops.append(count)
    if len(loops)>20:raise ValueError('Hole count exceeds20')
    return tuple(sorted(loops))

def validate(doc,source):
    mesh,pose=base_validate(doc,source)
    if mesh.CountFacets<4 or mesh.hasNonUniformOrientedFacets() or not boundaries(mesh):raise ValueError(tr('向きが整合した開口付きメッシュ4～20000面を指定してください。','Specify an oriented mesh with holes and4–20000 facets.'))
    return mesh,pose

def fill(doc,source,maximum=200):
    maximum=checked_count(maximum);mesh,pose=validate(doc,source);before=stamp(source);points,faces=mesh.Topology
    if max(boundaries(mesh))>maximum:raise ValueError(tr('全ての穴が指定上限以内である必要があります。','Every hole must fit the specified edge limit.'))
    mesh.fillupHoles(maximum);valid_mesh(mesh)
    afterp,afterf=mesh.Topology
    if afterp[:len(points)]!=points or afterf[:len(faces)]!=faces or len(afterf)<=len(faces):raise ValueError('Native filling changed original vertices/facets or added no facets')
    if not mesh.isSolid() or boundaries(mesh) or mesh.hasNonUniformOrientedFacets() or not math.isfinite(mesh.Volume) or mesh.Volume<=1e-9:raise ValueError('Filling did not produce a valid closed nonzero-volume mesh')
    for point in afterp:
        world=pose.multVec(point)
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (world.x,world.y,world.z)):raise ValueError('Filled world coordinates exceed supported bounds')
    if stamp(source)!=before:raise ValueError('Source changed during filling')
    return mesh,pose

def create(doc,source,maximum=200,expected=None):
    import model
    mesh,pose=fill(doc,source,maximum);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Filling differs from preview')
    with model.transaction(doc,tr('メッシュの穴を埋める','Fill Mesh Holes')):
        out=doc.addObject('Mesh::Feature','FilledMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('穴埋めメッシュ','Filled Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
