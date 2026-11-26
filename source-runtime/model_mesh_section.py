"""Independent editable sketch from local-Qwen native mesh-section geometry."""
import hashlib
import FreeCAD as App
import Part
from i18n import tr
from mesh_section_geometry import checked,frame
from mesh_section_tilt import section_data
from model_mesh_reverse import validate as base_validate,stamp

def validate(doc,source):
    mesh,pose=base_validate(doc,source)
    if mesh.hasNonUniformOrientedFacets():raise ValueError(tr('先にメッシュ法線を整合してください。','Harmonize mesh normals first.'))
    return mesh,pose

def centers(doc,source):
    mesh,pose=validate(doc,source);points=[pose.multVec(v) for v in mesh.Topology[0]]
    return {plane:(min(getattr(v,axis) for v in points)+max(getattr(v,axis) for v in points))/2 for plane,axis in (('XY','z'),('XZ','y'),('YZ','x'))}

def fingerprint(segments,placement):
    values=(tuple(placement.Base),tuple(placement.Rotation.Q),tuple((tuple(a),tuple(b)) for a,b in segments))
    return hashlib.sha256(repr(values).encode()).hexdigest()

def section(doc,source,plane='XY',position=0,angle_x=0,angle_y=0):
    plane,position=checked(plane,position);mesh,pose=validate(doc,source);before=stamp(source)
    segments,placement=section_data(mesh,pose,plane,position,angle_x,angle_y)
    if stamp(source)!=before:raise ValueError('Source changed during sectioning')
    return segments,placement

def create(doc,source,plane='XY',position=0,expected=None,*,angle_x=0,angle_y=0):
    import model,Sketcher
    segments,placement=section(doc,source,plane,position,angle_x,angle_y);before=stamp(source);visible=source.Visibility
    if expected is not None and fingerprint(segments,placement)!=expected:raise ValueError('Section differs from preview')
    with model.transaction(doc,tr('メッシュ断面スケッチ','Mesh Section Sketch')):
        out=doc.addObject('Sketcher::SketchObject','MeshSectionSketch');out.addGeometry([Part.LineSegment(a,b) for a,b in segments],False);out.Placement=placement;out.Label=tr('メッシュ断面','Mesh Section');doc.recompute()
        if out.GeometryCount!=len(segments) or out.ConstraintCount or out.OutList or out.Shape.isNull() or not out.Shape.isValid():raise ValueError('Invalid section sketch')
        for i,((a,b),g) in enumerate(zip(segments,out.Geometry)):
            if (g.StartPoint-a).Length>1e-7 or (g.EndPoint-b).Length>1e-7 or out.getConstruction(i):raise ValueError('Created sketch differs from section lines')
        if (out.Placement.Base-placement.Base).Length>1e-7 or any((out.Placement.Rotation.multVec(v)-placement.Rotation.multVec(v)).Length>1e-10 for v in (App.Vector(1,0,0),App.Vector(0,1,0))):raise ValueError('Sketch frame changed')
        if stamp(source)!=before or source.Visibility!=visible:raise ValueError('Source changed during sketch creation')
        out.Visibility=True
    return out
