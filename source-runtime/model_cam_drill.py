"""One vertical cylindrical hole, isolated native drilling job snapshot."""
import math,hashlib,sys
from pathlib import Path
import FreeCAD as App,Part,model
from cam_drill_values import validate_drill_depths

def resources(job,active=True):
    if not job or (active and job.Document!=App.ActiveDocument) or not (getattr(job,'FullArcCAMSetup',False) or getattr(job,'FullArcCAMDrillSetup',False)):raise ValueError('Choose a machining setup')
    if len(job.Model.Group)!=1 or len(job.Tools.Group)!=1:raise ValueError('One model and tool required')
    source=job.Model.Group[0];tc=job.Tools.Group[0];refs=[source,job.Stock,tc,tc.Tool]+list(getattr(source,'Objects',[]))
    for x in refs:
        if not x or any(v in x.State for v in ('Invalid','Error','Touched')):raise ValueError('Recompute valid inputs')
        if hasattr(x,'Shape') and (x.Shape.isNull() or not x.Shape.isValid()):raise ValueError('Invalid shape')
    if len(source.Shape.Solids)!=1 or len(source.Shape.Faces)>200:raise ValueError('One solid,max200faces')
    for x in (source,job.Stock):
        parent=x.getGlobalPlacement().multiply(x.Placement.inverse())
        if parent.Base.Length>1e-7 or abs(parent.Rotation.Angle)>1e-9:raise ValueError('Root CAM model required')
        bb=x.Shape.BoundBox
        if any(not math.isfinite(v) or abs(v)>1e6 for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)):raise ValueError('Coordinates outside range')
    if any(not math.isfinite(float(v)) or float(v)<=0 for v in (tc.VertFeed.Value,tc.HorizFeed.Value,tc.SpindleSpeed)):raise ValueError('Positive finite feed and spindle required')
    return source,tc,refs

def hole(job,index,active=True):
    source,tc,refs=resources(job,active)
    if type(index) is not int or not 1<=index<=len(source.Shape.Faces):raise ValueError('Invalid FaceN')
    face=source.Shape.Faces[index-1];surf=face.Surface;bb=face.BoundBox;top=source.Shape.BoundBox.ZMax
    if not isinstance(surf,Part.Cylinder) or abs(surf.Axis.z)<1-1e-9 or abs(bb.ZMax-top)>1e-7 or bb.ZLength<.001:raise ValueError('Vertical cylindrical hole opening at model top required')
    if not .01<=2*surf.Radius<=1000 or abs(face.Area-2*math.pi*surf.Radius*bb.ZLength)>max(1e-7,face.Area*1e-9):raise ValueError('Full cylindrical wall required')
    x=surf.Center.x;y=surf.Center.y;radius=surf.Radius
    cavity=Part.makeCylinder(radius,bb.ZLength,App.Vector(x,y,bb.ZMin));tol=max(1e-7,cavity.Volume*1e-9)
    if cavity.common(source.Shape).Volume>tol:raise ValueError('Not an empty cylindrical hole')
    thick=min(.001,radius*.001);wall=Part.makeCylinder(radius+thick,bb.ZLength,App.Vector(x,y,bb.ZMin)).cut(cavity)
    if wall.cut(source.Shape).Volume>max(1e-9,wall.Volume*1e-6):raise ValueError('Hole must be enclosed by solid walls')
    return source,tc,refs,(x,y,bb.ZMin,top,2*radius)

def candidates(job):
    source,tc,refs=resources(job);out=[]
    for i in range(1,len(source.Shape.Faces)+1):
        try:hole(job,i)
        except ValueError:continue
        out.append(i)
    return out

def signature(job,index):
    source,tc,refs,data=hole(job,index)
    return (job.Document.Name,job.Name,index,tuple((x.Name,hashlib.sha256(x.Shape.exportBrepToString().encode()).hexdigest()) for x in refs if hasattr(x,'Shape')),tc.VertFeed.Value,tc.HorizFeed.Value,float(tc.SpindleSpeed),int(tc.ToolNumber))

def defaults(job,index):
    *_,data=hole(job,index);top=job.Stock.Shape.BoundBox.ZMax
    return dict(start=top,final=data[2],retract=top+3,clearance=top+5)

def parameters(job,index,start,final,retract,clearance,active=True):
    values=validate_drill_depths(start,final,retract,clearance);source,tc,refs,data=hole(job,index,active)
    if values['final']<data[2]-1e-7 or values['final']>=data[3] or values['start']<job.Stock.Shape.BoundBox.ZMax-1e-7:raise ValueError('Depths must respect hole bottom and stock top')
    if values['start']-values['final']>100:raise ValueError('Limited to100mm depth')
    return source,tc,refs,data,values

def check_path(op,data,values,feed):
    commands=op.Path.Commands
    if not commands or len(commands)>1000:raise ValueError('Empty or excessive path')
    cycles=[c for c in commands if c.Name=='G81']
    if len(cycles)!=1:raise ValueError('Exactly one G81 required')
    for key,expected in [('X',data[0]),('Y',data[1]),('Z',values['final']),('R',values['retract']),('F',feed)]:
        if abs(cycles[0].Parameters.get(key,float('inf'))-expected)>1e-7:raise ValueError('Native cycle mismatch:'+key)
    for c in commands:
        if not c.Name.startswith('(') and c.Name not in ('G0','G90','G98','G81','G80'):raise ValueError('Unsupported native cycle')
        if any(not math.isfinite(v) for v in c.Parameters.values()):raise ValueError('Nonfinite native cycle')
        if c.Name=='G0':
            for key,expected in [('X',data[0]),('Y',data[1])]:
                if key in c.Parameters and abs(c.Parameters[key]-expected)>1e-7:raise ValueError('Wrong rapid position')
            if 'Z' in c.Parameters and not values['retract']-1e-7<=c.Parameters['Z']<=values['clearance']+1e-7:raise ValueError('Unsafe rapid height')
    names=[c.Name for c in commands];assert 'G98' in names and 'G80' in names

def create(job,index,start,final,retract,clearance,expected=None):
    source,tc,refs,data,values=parameters(job,index,start,final,retract,clearance)
    if expected is not None and signature(job,index)!=expected:raise ValueError('Setup changed;reopen')
    doc=job.Document;shape=source.Shape.copy();stock=job.Stock.Shape.copy();extensions={k:getattr(job.Stock,k).Value for k in ('ExtXneg','ExtXpos','ExtYneg','ExtYpos','ExtZneg','ExtZpos')};feed=tc.HorizFeed.Value;plunge=tc.VertFeed.Value;rpm=tc.SpindleSpeed;number=tc.ToolNumber
    cam=str(Path(App.getHomePath())/'Mod/CAM')
    if cam not in sys.path:sys.path.append(cam)
    from Path.Tool.toolbit import ToolBit
    from cam_drill_proxy import GuardedDrilling
    import model_cam_setup as setup
    stage=App.newDocument('DrillingStage')
    try:
        s=stage.addObject('Part::Feature','Input');s.Shape=shape;stage.recompute();j=setup._build(s,diameter=data[4],feed=feed*60,plunge=plunge*60,rpm=rpm,tool_number=number)
        j.FullArcCAMSetup=False;j.addProperty('App::PropertyBool','FullArcCAMDrillSetup');j.FullArcCAMDrillSetup=True
        for k,v in extensions.items():setattr(j.Stock,k,v)
        stage.recompute()
        if abs(j.Stock.Shape.Volume-stock.Volume)>max(1e-7,stock.Volume*1e-9):raise ValueError('Stock snapshot mismatch')
        tool=ToolBit.from_shape_id('drill').attach_to_doc(stage);tool.Diameter=data[4];tool.Length=max(120.,values['start']-values['final']+20);tool.TipAngle=118
        newtc=j.Tools.Group[0];oldtool=newtc.Tool;newtc.Tool=tool;stage.recompute();stage.removeObject(oldtool.Name);stage.recompute()
        src=j.Model.Group[0];op=stage.addObject('Path::FeaturePython','Drilling');GuardedDrilling(op,'Drilling',j);op.ToolController=newtc
        op.addProperty('App::PropertyInteger','FullArcDrillFace');op.FullArcDrillFace=index
        op.addProperty('App::PropertyLinkList','FullArcInputs');op.FullArcInputs=[src,j.Stock,newtc,tool]+list(src.Objects)
        op.Base=[(src,['Face'+str(index)])]
        for key,prop in [('start','StartDepth'),('final','FinalDepth'),('retract','SafeHeight'),('retract','RetractHeight'),('clearance','ClearanceHeight')]:op.setExpression(prop,None);setattr(op,prop,values[key])
        op.PeckEnabled=False;op.DwellEnabled=False;op.ExtraOffset='None';op.AddTipLength=False;op.KeepToolDown=False;op.chipBreakEnabled=False;op.feedRetractEnabled=False
        stage.recompute();check_path(op,data,values,plunge)
        if 'Invalid' in op.State:raise ValueError('Native drilling invalid')
        op.addProperty('App::PropertyBool','FullArcCAMDrilling');op.FullArcCAMDrilling=True
        App.setActiveDocument(doc.Name)
        with model.transaction(doc,'Drilling'):
            copy=doc.copyObject(j,True);doc.recompute();ops=[o for o in copy.Operations.Group if getattr(o,'FullArcCAMDrilling',False)]
            if len(ops)!=1:raise ValueError('Operation transfer failed')
            check_path(ops[0],data,values,plunge)
            for x in copy.Model.Group+[copy.Stock,copy.Tools.Group[0].Tool]:x.ViewObject.Visibility=False
        return ops[0]
    finally:App.closeDocument(stage.Name);App.setActiveDocument(doc.Name)
