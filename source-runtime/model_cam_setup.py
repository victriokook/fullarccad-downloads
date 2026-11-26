"""Offline native CAM job from an independent world-shape snapshot."""
import sys,math
from pathlib import Path
import FreeCAD as App
import model
from cam_setup_values import validate_setup

def source_shape(source):
    if not source or source.Document!=App.ActiveDocument or source.isDerivedFrom('App::Link') or not hasattr(source,'Shape'):raise ValueError('Select a whole solid in the current document')
    if any(x in source.State for x in ('Error','Invalid','Touched')):raise ValueError('Recompute a valid source first')
    shape=model.world_shape(source)
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or len(shape.Faces)>2000:raise ValueError('Select one valid solid with at most 2000 faces')
    bb=shape.BoundBox
    if any(not math.isfinite(x) or abs(x)>1e6 for x in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)):raise ValueError('Source outside coordinate limits')
    return shape

def signature(source):return (source.Document.Name,source.Name,source_shape(source).exportBrepToString())

def _build(source,margin=1.,diameter=5.,feed=300.,plunge=100.,rpm=3000.,tool_number=1,expected=None):
    values=validate_setup(margin,diameter,feed,plunge,rpm,tool_number);shape=source_shape(source)
    if expected is not None and signature(source)!=expected:raise ValueError('Source changed; reopen')
    cam=str(Path(App.getHomePath())/'Mod/CAM')
    if cam not in sys.path:sys.path.append(cam)
    from Path.Main import Job
    doc=source.Document
    with model.transaction(doc,'Machining Setup'):
        snapshot=doc.addObject('Part::Feature','MachiningSnapshot');snapshot.Shape=shape;snapshot.Label='Machining model (independent copy)'
        job=Job.Create('MachiningJob',[snapshot]);job.addProperty('App::PropertyBool','FullArcCAMSetup');job.FullArcCAMSetup=True;job.addProperty('App::PropertyString','SourceDescription');job.SourceDescription=source.Label+' (independent snapshot; no automatic source updates)'
        for key in ('ExtXneg','ExtXpos','ExtYneg','ExtYpos','ExtZneg','ExtZpos'):setattr(job.Stock,key,values['margin'])
        if len(job.Tools.Group)!=1:raise ValueError('Expected one native tool controller')
        tc=job.Tools.Group[0];tc.Tool.Diameter=values['diameter'];tc.Tool.ShankDiameter=values['diameter'];tc.ToolNumber=tool_number;tc.HorizFeed=str(values['feed'])+' mm/min';tc.VertFeed=str(values['plunge'])+' mm/min';tc.SpindleSpeed=values['rpm'];doc.recompute()
        stock=job.Stock.Shape;bb=shape.BoundBox;expected_volume=(bb.XLength+2*margin)*(bb.YLength+2*margin)*(bb.ZLength+2*margin)
        if stock.isNull() or not stock.isValid() or abs(stock.Volume-expected_volume)>max(1e-6,expected_volume*1e-9):raise ValueError('Native stock creation failed')
        if abs(tc.Tool.Diameter.Value-values['diameter'])>1e-9 or tc.Tool.Shape.isNull() or not tc.Tool.Shape.isValid():raise ValueError('Native tool creation failed')
        if any('Error' in o.State or 'Invalid' in o.State for o in (job,job.Stock,tc,tc.Tool)):raise ValueError('Native CAM resource invalid')
        snapshot.ViewObject.Visibility=False
        for obj in job.Model.Group:obj.ViewObject.Visibility=False
        job.Stock.ViewObject.Visibility=False;tc.Tool.ViewObject.Visibility=False
    return job

def create(source,margin=1.,diameter=5.,feed=300.,plunge=100.,rpm=3000.,tool_number=1,expected=None):
    values=validate_setup(margin,diameter,feed,plunge,rpm,tool_number);shape=source_shape(source);doc=source.Document;label=source.Label
    if expected is not None and signature(source)!=expected:raise ValueError('Source changed; reopen')
    stage=App.newDocument('FullArcCAMStaging')
    try:
        temp=stage.addObject('Part::Feature','Input');temp.Shape=shape;temp.Label=label;stage.recompute();native=_build(temp,**values)
        App.setActiveDocument(doc.Name)
        with model.transaction(doc,'Machining Setup'):
            job=doc.copyObject(native,True);doc.recompute()
            if not job.Stock.Shape.isValid() or len(job.Tools.Group)!=1 or not job.Tools.Group[0].Tool.Shape.isValid():raise ValueError('CAM resource transfer failed')
            job.Stock.ViewObject.Visibility=False
            for obj in job.Model.Group:obj.ViewObject.Visibility=False
        return job
    finally:
        App.closeDocument(stage.Name);App.setActiveDocument(doc.Name)
