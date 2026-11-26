"""Read-only whole-mesh diagnostics, including defective input topology."""
import math
import FreeCAD as App
from i18n import tr
from model_mesh_refine import stamp
from mesh_inspect_geometry import evaluate

def validate(doc,source):
    if (doc is None or App.ActiveDocument is not doc or source is None or source.Document is not doc or doc.getObject(source.Name) is not source or source.TypeId!='Mesh::Feature' or getattr(source,'Error','') or any(s in source.State for s in ('Error','Invalid'))):raise ValueError(tr('現在の文書のメッシュ全体を1つ選択してください。','Select one whole mesh in the active document.'))
    if not 1<=source.Mesh.CountFacets<=20000:raise ValueError(tr('面数は1～20000に制限しています。','Facet count must be1–20000.'))
    parent=source.getParentGeoFeatureGroup()
    while parent:
        if getattr(parent,'Error','') or any(s in parent.State for s in ('Error','Invalid')):raise ValueError('Invalid mesh container')
        parent=parent.getParentGeoFeatureGroup()
    mesh=source.Mesh.copy();mesh.Placement=App.Placement();pose=source.getGlobalPlacement()
    for point in mesh.Topology[0]:
        for vector in (point,pose.multVec(point)):
            if any(not math.isfinite(v) or abs(v)>1e6 for v in vector):raise ValueError('Mesh coordinates exceed the supported local/world bounds')
    return mesh

def inspect(doc,source):
    mesh=validate(doc,source);before=stamp(source);result=evaluate(mesh)
    if stamp(source)!=before:raise ValueError('Source changed during inspection')
    return result
