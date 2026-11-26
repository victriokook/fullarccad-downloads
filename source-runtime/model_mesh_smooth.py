"""Independent Laplace smoothing using nativeMesh;uses226 validation/frame."""
import FreeCAD as App
from i18n import tr
from mesh_smooth_values import checked
from model_mesh_reduce import validate,valid_mesh,stamp,fingerprint


def smooth(doc,source,iterations,strength):
    iterations,strength=checked(iterations,strength);mesh,pose=validate(doc,source);before=stamp(source);points,facets=mesh.Topology
    mesh.smooth(Method='Laplace',Iteration=iterations,Lambda=strength);valid_mesh(mesh)
    after,triangles=mesh.Topology
    if triangles!=facets or len(points)!=len(after):raise ValueError('Native smoothing changed mesh connectivity')
    if max((a-b).Length for a,b in zip(points,after))<=1e-7:raise ValueError(tr('頂点が変化しません。設定を変更してください。','Vertices did not change. Change the settings.'))
    if stamp(source)!=before:raise ValueError('Source changed during smoothing')
    return mesh,pose


def create(doc,source,iterations,strength,expected=None):
    import model
    mesh,pose=smooth(doc,source,iterations,strength);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Smoothing differs from preview')
    with model.transaction(doc,tr('メッシュを平滑化','Smooth Mesh')):
        out=doc.addObject('Mesh::Feature','SmoothedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('平滑化メッシュ','Smoothed Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
