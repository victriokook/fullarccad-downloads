import sys,math,hashlib
from pathlib import Path
import FreeCAD as App
import Part,model
from cam_depth_values import validate_depths

def inputs(job,active=True):
    if not job or (active and job.Document!=App.ActiveDocument) or not getattr(job,'FullArcCAMSetup',False):raise ValueError('Choose a FullArcCAD machining setup')
    if len(job.Model.Group)!=1 or len(job.Tools.Group)!=1:raise ValueError('One model and one tool required')
    source=job.Model.Group[0];tc=job.Tools.Group[0]
    objects=[source,job.Stock,tc,tc.Tool]+list(getattr(source,'Objects',[]))
    for obj in objects:
        if any(x in obj.State for x in ('Invalid','Error','Touched')):raise ValueError('Recompute valid CAM inputs first')
        if hasattr(obj,'Shape') and (obj.Shape.isNull() or not obj.Shape.isValid()):raise ValueError('Invalid CAM geometry')
    shape=model.world_shape(source);bb=shape.BoundBox
    if len(shape.Solids)!=1 or len(shape.Edges)>200 or bb.ZLength<=1e-6:raise ValueError('One vertical prism with at most 200 edges required')
    bottoms=[f for f in shape.Faces if isinstance(f.Surface,Part.Plane) and abs(f.BoundBox.ZMin-bb.ZMin)<1e-7 and f.BoundBox.ZLength<1e-7]
    if len(bottoms)!=1 or len(bottoms[0].Wires)!=1:raise ValueError('One horizontal bottom without holes required')
    if any(not isinstance(edge.Curve,Part.Line) for edge in bottoms[0].Edges):raise ValueError('Straight polygon contours only;curved contours pending precision verification')
    prism=bottoms[0].extrude(App.Vector(0,0,bb.ZLength));tol=max(1e-7,shape.Volume*1e-9)
    if shape.cut(prism).Volume>tol or prism.cut(shape).Volume>tol:raise ValueError('Constant vertical cross section required')
    if tc.Tool.Diameter.Value<=0 or tc.HorizFeed.Value<=0 or tc.VertFeed.Value<=0 or tc.SpindleSpeed<=0:raise ValueError('Positive tool diameter,feeds and spindle required')
    return source,tc

def signature(job):
    source,tc=inputs(job)
    return (job.Document.Name,job.Name,hashlib.sha256(model.world_shape(source).exportBrepToString().encode()).hexdigest(),job.Stock.Shape.exportBrepToString(),tuple((x.Name,x.Shape.exportBrepToString()) for x in getattr(source,'Objects',[])),float(tc.Tool.Diameter.Value),float(tc.HorizFeed.Value),float(tc.VertFeed.Value),float(tc.SpindleSpeed),int(tc.ToolNumber))

def defaults(job):
    source,tc=inputs(job);top=job.Stock.Shape.BoundBox.ZMax
    return dict(start=top,final=source.Shape.BoundBox.ZMin,step=min(3.,max(.001,top-source.Shape.BoundBox.ZMin)),safe=top+3,clearance=top+5)

def create(job,start,final,step,safe,clearance,expected=None):
    values=validate_depths(start,final,step,safe,clearance);source,tc=inputs(job);stamp=signature(job)
    if expected is not None and stamp!=expected:raise ValueError('Setup changed; reopen')
    bb=source.Shape.BoundBox
    if final<bb.ZMin-1e-7 or final>=bb.ZMax or start<bb.ZMax-1e-7 or safe<=job.Stock.Shape.BoundBox.ZMax:raise ValueError('Depth must remain inside model Z range;start above model,safe above stock')
    cam=str(Path(App.getHomePath())/'Mod/CAM')
    if cam not in sys.path:sys.path.append(cam)
    from cam_profile_proxy import GuardedProfile
    with model.transaction(job.Document,'2D Contour'):
        op=job.Document.addObject('Path::FeaturePython','Contour');GuardedProfile(op,'Contour',job);op.ToolController=tc
        op.addProperty('App::PropertyLinkList','FullArcInputs');op.FullArcInputs=[source,job.Stock,tc,tc.Tool]+list(getattr(source,'Objects',[]));op.setEditorMode('FullArcInputs',2)
        for key,name in [('start','StartDepth'),('final','FinalDepth'),('step','StepDown'),('safe','SafeHeight'),('clearance','ClearanceHeight')]:op.setExpression(name,None);setattr(op,name,values[key])
        op.Side='Outside';op.UseComp=True;op.processPerimeter=True;op.processHoles=False;op.processCircles=False;op.Direction='CW';job.Document.recompute()
        commands=op.Path.Commands
        if not commands or len(commands)>100000 or not any(c.Name in ('G1','G2','G3') for c in commands):raise ValueError('Native contour has no cutting moves or exceeds command limit')
        if any(not math.isfinite(float(v)) or (k in ('X','Y','Z','I','J','K') and abs(v)>1e6) for c in commands for k,v in c.Parameters.items()):raise ValueError('Invalid native command coordinate')
        if 'Error' in op.State or 'Invalid' in op.State:raise ValueError('Native profile failed')
        op.addProperty('App::PropertyBool','FullArcCAMContour');op.FullArcCAMContour=True
    return op
