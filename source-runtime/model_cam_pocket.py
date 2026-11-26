"""Native PocketShape,limited to enclosed world-XY rectangular cavities."""
import sys,math,hashlib
from pathlib import Path
import FreeCAD as App
import Part,model
from cam_depth_values import validate_depths
from cam_pocket_values import validate_stepover

def resources(job,active=True):
    if not job or (active and job.Document!=App.ActiveDocument) or not getattr(job,'FullArcCAMSetup',False):raise ValueError('Choose a FullArcCAD machining setup')
    if not job.Model or not job.Stock or not job.Tools or len(job.Model.Group)!=1 or len(job.Tools.Group)!=1:raise ValueError('One model,stock and tool required')
    source=job.Model.Group[0];tc=job.Tools.Group[0]
    if not tc.Tool:raise ValueError('Missing tool')
    refs=[source,job.Stock,tc,tc.Tool]+list(getattr(source,'Objects',[]))
    for obj in refs:
        if not obj or any(x in obj.State for x in ('Invalid','Error','Touched')):raise ValueError('Recompute valid CAM inputs first')
        if hasattr(obj,'Shape') and (obj.Shape.isNull() or not obj.Shape.isValid()):raise ValueError('Invalid CAM geometry')
    if len(source.Shape.Solids)!=1 or len(source.Shape.Faces)>200:raise ValueError('One solid with at most200faces required')
    for obj in (source,job.Stock):
        parent=obj.getGlobalPlacement().multiply(obj.Placement.inverse())
        if parent.Base.Length>1e-7 or abs(parent.Rotation.Angle)>1e-9:raise ValueError('Root machining model and stock required')
        bb=obj.Shape.BoundBox
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)):raise ValueError('CAM geometry outside bounds')
    if any(not math.isfinite(float(v)) or float(v)<=0 for v in (tc.Tool.Diameter.Value,tc.HorizFeed.Value,tc.VertFeed.Value,tc.SpindleSpeed)):raise ValueError('Positive finite tool,feeds and spindle required')
    return source,tc,refs

def rectangle(job,face_index,active=True):
    source,tc,refs=resources(job,active)
    if type(face_index) is not int or not 1<=face_index<=len(source.Shape.Faces):raise ValueError('Select a valid bottom FaceN')
    shape=source.Shape;face=shape.Faces[face_index-1];bb=face.BoundBox;top=shape.BoundBox.ZMax;depth=top-bb.ZMin
    if not isinstance(face.Surface,Part.Plane) or bb.ZLength>1e-7 or face.normalAt(0,0).z<1-1e-7 or len(face.Wires)!=1 or len(face.Edges)!=4 or depth<=1e-5:raise ValueError('Select a horizontal rectangular pocket bottom')
    if abs(face.Area-bb.XLength*bb.YLength)>max(1e-7,face.Area*1e-9):raise ValueError('World XY rectangle required')
    for edge in face.Edges:
        if not isinstance(edge.Curve,Part.Line):raise ValueError('Straight rectangular sides required')
        delta=edge.Vertexes[-1].Point-edge.Vertexes[0].Point
        if abs(delta.z)>1e-7 or (abs(delta.x)>1e-7 and abs(delta.y)>1e-7):raise ValueError('Rectangle sides must align with world X/Y')
    validate_stepover(40.,float(tc.Tool.Diameter.Value),bb.XLength,bb.YLength)
    cavity=Part.makeBox(bb.XLength,bb.YLength,depth,App.Vector(bb.XMin,bb.YMin,bb.ZMin));tol=max(1e-7,cavity.Volume*1e-9)
    if cavity.common(shape).Volume>tol:raise ValueError('Pocket contains an island,overhang or tapered wall')
    thickness=min(.001,bb.XLength*.001,bb.YLength*.001)
    for x,y,w,h in [(bb.XMin-thickness,bb.YMin,thickness,bb.YLength),(bb.XMax,bb.YMin,thickness,bb.YLength),(bb.XMin,bb.YMin-thickness,bb.XLength,thickness),(bb.XMin,bb.YMax,bb.XLength,thickness)]:
        slab=Part.makeBox(w,h,depth,App.Vector(x,y,bb.ZMin))
        if slab.cut(shape).Volume>max(1e-9,slab.Volume*1e-6):raise ValueError('Closed vertical walls up to model top required')
    return source,tc,refs,bb,top

def candidates(job):
    source,tc,refs=resources(job);result=[]
    for index in range(1,len(source.Shape.Faces)+1):
        try:rectangle(job,index)
        except ValueError:continue
        result.append(index)
    return result

def signature(job,face_index):
    source,tc,refs,bb,top=rectangle(job,face_index)
    shapes=tuple((x.Name,hashlib.sha256(x.Shape.exportBrepToString().encode()).hexdigest()) for x in refs if hasattr(x,'Shape'))
    return (job.Document.Name,job.Name,face_index,shapes,float(tc.Tool.Diameter.Value),float(tc.HorizFeed.Value),float(tc.VertFeed.Value),float(tc.SpindleSpeed),int(tc.ToolNumber))

def parameters(job,face_index,start,final,step,safe,clearance,stepover,active=True):
    values=validate_depths(start,final,step,safe,clearance);source,tc,refs,bb,top=rectangle(job,face_index,active);diam=float(tc.Tool.Diameter.Value);percent=validate_stepover(stepover,diam,bb.XLength,bb.YLength)
    if values['final']<bb.ZMin-1e-7 or values['final']>=top or values['start']<top-1e-7 or values['safe']<=job.Stock.Shape.BoundBox.ZMax:raise ValueError('Depths must respect pocket floor,model top and stock top')
    if tc.Tool.CuttingEdgeHeight.Value<values['start']-values['final']:raise ValueError('Tool cutting edge is too short for the depth')
    rings=math.ceil(min(bb.XLength,bb.YLength)/(2*diam*percent/100))+1
    if rings*math.ceil((values['start']-values['final'])/values['step'])>5000:raise ValueError('Pocket path complexity exceeds limit')
    return source,tc,refs,bb,values,percent

def defaults(job,face_index):
    source,tc,refs,bb,top=rectangle(job,face_index);start=job.Stock.Shape.BoundBox.ZMax
    return dict(start=start,final=bb.ZMin,step=min(2.,start-bb.ZMin),safe=start+3,clearance=start+5,stepover=40.)

def check_path(op,bb,radius,values):
    commands=op.Path.Commands
    if not commands or len(commands)>100000:raise ValueError('Empty or excessive native path')
    position={};cuts=0;tol=2e-6
    for command in commands:
        if command.Name.startswith('('):continue
        if command.Name not in ('G0','G1'):raise ValueError('Only linear native pocket motions supported')
        args=command.Parameters
        if any(not math.isfinite(float(v)) for v in args.values()):raise ValueError('Nonfinite native command')
        target={**position,**{k:float(v) for k,v in args.items() if k in 'XYZ'}}
        if command.Name=='G0' and any(k in args and abs(args[k]-position.get(k,args[k]))>tol for k in ('X','Y')) and (position.get('Z',-1e9)<values['safe']-tol or target.get('Z',-1e9)<values['safe']-tol):raise ValueError('Rapid XY move below safe height')
        if 'X' in target and not bb.XMin+radius-tol<=target['X']<=bb.XMax-radius+tol:raise ValueError('Tool center crosses pocket X boundary')
        if 'Y' in target and not bb.YMin+radius-tol<=target['Y']<=bb.YMax-radius+tol:raise ValueError('Tool center crosses pocket Y boundary')
        if 'Z' in target and not values['final']-tol<=target['Z']<=values['clearance']+tol:raise ValueError('Native path outside Z limits')
        if command.Name=='G1':
            if not all(k in target for k in 'XYZ') or args.get('F',0)<=0:raise ValueError('Cut move lacks position or positive feed')
            cuts+=1
        position=target
    if not cuts:raise ValueError('No cutting moves')

def create(job,face_index,start,final,step,safe,clearance,stepover=40.,expected=None):
    source,tc,refs,bb,values,percent=parameters(job,face_index,start,final,step,safe,clearance,stepover)
    if expected is not None and signature(job,face_index)!=expected:raise ValueError('Setup changed;reopen')
    from cam_pocket_proxy import GuardedPocket
    with model.transaction(job.Document,'2D Pocket'):
        op=job.Document.addObject('Path::FeaturePython','Pocket');GuardedPocket(op,'Pocket',job);op.ToolController=tc
        op.addProperty('App::PropertyLinkList','FullArcInputs');op.FullArcInputs=refs;op.setEditorMode('FullArcInputs',2)
        op.addProperty('App::PropertyInteger','FullArcPocketFace');op.FullArcPocketFace=face_index;op.setEditorMode('FullArcPocketFace',2)
        op.Base=[(source,['Face'+str(face_index)])]
        for key,name in [('start','StartDepth'),('final','FinalDepth'),('step','StepDown'),('safe','SafeHeight'),('clearance','ClearanceHeight')]:op.setExpression(name,None);setattr(op,name,values[key])
        op.StepOver=int(percent);op.ClearingPattern='Offset';op.UseOutline=False;op.UseRestMachining=False;op.ExtraOffset=0;op.KeepToolDown=False;op.UseStartPoint=False;op.FinishDepth=0
        job.Document.recompute();check_path(op,bb,tc.Tool.Diameter.Value/2,values)
        if 'Error' in op.State or 'Invalid' in op.State:raise ValueError('Native pocket failed')
        op.addProperty('App::PropertyBool','FullArcCAMPocket');op.FullArcCAMPocket=True
    return op
