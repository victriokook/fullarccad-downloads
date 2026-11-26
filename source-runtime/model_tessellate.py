"""Independent CAD-to-mesh using reviewed local-Qwen native tessellation."""
import math
import FreeCAD as App
import Part
from i18n import tr
from tessellate_geometry import checked,tessellate as native_tessellate
from model_mesh_reduce import fingerprint
from surface_isocurve_limits import validate_complexity

def stamp(source):
    parents=[];current=source.getParentGeoFeatureGroup()
    while current:
        parents.append((current.Name,str(current.Placement),tuple(v for v in current.State if v in ('Error','Invalid')),str(getattr(current,'Error',''))));current=current.getParentGeoFeatureGroup()
    shape=source.Shape;box=shape.BoundBox
    return (shape.hashCode(),shape.isNull(),len(shape.Faces),shape.Area,shape.Volume,tuple(getattr(box,k) for k in ('XMin','YMin','ZMin','XMax','YMax','ZMax')),str(source.getGlobalPlacement()),tuple(parents),tuple(v for v in source.State if v in ('Error','Invalid')),str(getattr(source,'Error','')))

def validate(doc,source):
    if doc is None or App.ActiveDocument is not doc or source is None or source.Document is not doc or doc.getObject(source.Name) is not source or source.isDerivedFrom('App::Link') or getattr(source,'FluxCADInternal',False) or not hasattr(source,'Shape') or getattr(source,'Error','') or any(v in source.State for v in ('Error','Invalid')):raise ValueError(tr('現在文書のCAD形状全体を1つ選択してください。','Select one whole CAD shape in the active document.'))
    current=source.getParentGeoFeatureGroup()
    while current:
        if getattr(current,'Error','') or any(v in current.State for v in ('Error','Invalid')):raise ValueError('Repair parent container errors first')
        current=current.getParentGeoFeatureGroup()
    shape=source.Shape.copy();shape.Placement=App.Placement()
    if shape.isNull() or not shape.isValid() or shape.ShapeType not in ('Solid','Face','Shell') or not 1<=len(shape.Faces)<=200 or len(shape.Edges)>2000 or len(shape.Vertexes)>2000:raise ValueError('Use one valid Solid or open Face/Shell with1–200 faces;loose/compound shapes excluded')
    if shape.ShapeType=='Solid':
        if len(shape.Solids)!=1 or not math.isfinite(shape.Volume) or shape.Volume<=1e-9:raise ValueError('Use one outward positive-volume solid')
    elif shape.isClosed():raise ValueError('Closed Face/Shell is outside this command;use a Solid or open surface')
    if not 1e-7<shape.BoundBox.DiagonalLength<=10000:raise ValueError('Shape diagonal must be above1e-7 and at most10000mm')
    for face in shape.Faces:
        if isinstance(face.Surface,(Part.BSplineSurface,Part.BezierSurface)):
            v=face.Surface;validate_complexity(v.NbUPoles,v.NbVPoles,v.UDegree,v.VDegree)
    pose=source.getGlobalPlacement();world=shape.copy();world.Placement=pose
    for box in (shape.BoundBox,world.BoundBox):
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax)):raise ValueError('Local/world CAD bounds exceed ±1000000mm')
    return shape,pose

def defaults(doc,source):
    shape,pose=validate(doc,source);return max(.1,math.ceil(shape.BoundBox.DiagonalLength/2000*1e8)/1e8),20.

def tessellate(doc,source,linear=.1,angle=20):
    linear,angle=checked(linear,angle);shape,pose=validate(doc,source);before=stamp(source);mesh=native_tessellate(shape,linear,angle)
    for point in mesh.Topology[0]:
        if any(not math.isfinite(v) or abs(v)>1e6 for v in pose.multVec(point)):raise ValueError('World mesh coordinates exceed ±1000000mm')
    if stamp(source)!=before:raise ValueError('Source changed during tessellation')
    return mesh,pose

def create(doc,source,linear=.1,angle=20,expected=None):
    import model
    mesh,pose=tessellate(doc,source,linear,angle);before=stamp(source)
    if expected is not None and fingerprint(mesh)!=expected:raise ValueError('Tessellation differs from preview')
    with model.transaction(doc,tr('CAD形状からメッシュを作成','Create Mesh from CAD')):
        out=doc.addObject('Mesh::Feature','TessellatedMesh');out.Mesh=mesh;out.Placement=pose;out.Label=tr('CAD形状のメッシュ','Tessellated CAD Mesh');out.ViewObject.ShapeColor=source.ViewObject.ShapeColor;doc.recompute()
        actual=out.Mesh.copy();actual.Placement=App.Placement()
        if fingerprint(actual)!=fingerprint(mesh) or stamp(source)!=before or out.OutList:raise ValueError('Created mesh differs or source changed')
        if (out.getGlobalPlacement().Base-pose.Base).Length>1e-7 or any((out.getGlobalPlacement().Rotation.multVec(v)-pose.Rotation.multVec(v)).Length>1e-10 for v in (App.Vector(1,0,0),App.Vector(0,1,0))):raise ValueError('Created mesh placement differs')
        source.Visibility=False;out.Visibility=True
    return out
