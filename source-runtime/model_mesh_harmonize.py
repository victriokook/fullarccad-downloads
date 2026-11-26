"""Whole-mesh consistent orientation; does not guarantee outward normals."""
import FreeCAD as App
from i18n import tr
from model_mesh_reverse import valid_mesh,stamp,fingerprint,normal_lines,validate as base_validate
from mesh_harmonize_values import changed_indices

def validate(doc,source):
    mesh,pose=base_validate(doc,source)
    if mesh.CountFacets<2 or not mesh.hasNonUniformOrientedFacets():raise ValueError(tr('不整合な法線を持つ2面以上のメッシュを指定してください。','Specify a mesh with at least two facets and inconsistent normals.'))
    return mesh,pose

def harmonize(doc,source):
    mesh,pose=validate(doc,source);before=stamp(source);points,triangles=mesh.Topology;normals=[f.Normal for f in mesh.Facets]
    mesh.harmonizeNormals();valid_mesh(mesh)
    if mesh.Topology[0]!=points or mesh.hasNonUniformOrientedFacets():raise ValueError('Native harmonization changed vertices or left inconsistent normals')
    changed=changed_indices(triangles,mesh.Topology[1])
    if not changed:raise ValueError('Native harmonization made no changes')
    changed=set(changed)
    if any((f.Normal+normals[i] if i in changed else f.Normal-normals[i]).Length>1e-6 for i,f in enumerate(mesh.Facets)):raise ValueError('Normals do not match repaired winding')
    if stamp(source)!=before:raise ValueError('Source changed during harmonization')
    return mesh,pose

def create(doc,source,expected=None):
    import model
    mesh,pose=harmonize(doc,source);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Harmonization differs from preview')
    with model.transaction(doc,tr('メッシュ法線を整合','Harmonize Mesh Normals')):
        out=doc.addObject('Mesh::Feature','HarmonizedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('法線整合メッシュ','Harmonized Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        source.Visibility=False;out.Visibility=True
    return out
