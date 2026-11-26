"""Read-only native PathSimulator snapshot,linear endmill operations only."""
import math,hashlib
import FreeCAD as App,Path,PathSimulator
from cam_sim_values import validate_grid

def snapshot(op,resolution):
    if not op or op.Document!=App.ActiveDocument or not any(getattr(op,n,False) for n in ('FullArcCAMPocket','FullArcCAMFacing')):raise ValueError('Choose a FullArcCAD pocket or facing operation')
    if not op.Active or any(x in op.State for x in ('Touched','Invalid','Error')):raise ValueError('Recompute an active valid operation')
    placement=getattr(op,'Placement',App.Placement())
    if placement.Base.Length>1e-7 or abs(placement.Rotation.Angle)>1e-9:raise ValueError('Unmoved operation required')
    pending=list(op.InList);seen=set()
    while pending:
        parent=pending.pop()
        if parent.Name in seen:continue
        seen.add(parent.Name)
        if parent.isDerivedFrom('App::Part'):raise ValueError('Root machining operation required')
        pending.extend(parent.InList)
    job=op.Proxy.getJob(op);tool=op.ToolController.Tool
    refs=list(op.FullArcInputs)
    for obj in refs:
        if not obj or any(x in obj.State for x in ('Touched','Invalid','Error')):raise ValueError('Invalid simulation input')
        if hasattr(obj,'Shape') and (obj.Shape.isNull() or not obj.Shape.isValid()):raise ValueError('Invalid simulation geometry')
    if tool.Proxy.get_shape_name().lower()!='endmill':raise ValueError('Endmill only')
    stock=job.Stock.Shape.copy();bb=stock.BoundBox;validate_grid((bb.XLength,bb.YLength,bb.ZLength),resolution)
    if any(abs(v)>10000 for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)):raise ValueError('Simulation bounds limited to10000mm')
    commands=op.Path.Commands
    if not 1<=len(commands)<=2000:raise ValueError('Simulation supports1..2000commands')
    copies=[];pos={};travel=0.;cut=False
    for cmd in commands:
        if cmd.Name.startswith('('):continue
        if cmd.Name not in ('G0','G1'):raise ValueError('Only G0/G1 linear paths supported')
        params=dict(cmd.Parameters)
        if any(k not in ('X','Y','Z','F') or not math.isfinite(v) or abs(v)>10000 for k,v in params.items()):raise ValueError('Unsupported command or coordinate')
        new={**pos,**{k:v for k,v in params.items() if k in ('X','Y','Z')}}
        if not copies and ('Z' not in params or params['Z']<=bb.ZMax):raise ValueError('Initial clearance move required')
        if cmd.Name=='G1' and not all(k in new for k in ('X','Y','Z')):raise ValueError('Unknown cutting position')
        if all(k in pos and k in new for k in ('X','Y','Z')):travel+=math.dist(tuple(pos[k] for k in 'XYZ'),tuple(new[k] for k in 'XYZ'))
        pos=new;cut=cut or cmd.Name=='G1';copies.append(Path.Command(cmd.Name,params))
    if not cut or travel/resolution>200000:raise ValueError('Missing cuts or excessive travel')
    stamp=(op.Document.Name,op.Name,op.Path.toGCode(),tuple((x.Name,hashlib.sha256(x.Shape.exportBrepToString().encode()).hexdigest()) for x in refs if hasattr(x,'Shape')),tool.Proxy.get_shape_name(),tuple(str(x.State) for x in refs))
    return stock,tool.Shape.copy(),copies,stamp

class Simulation:
    def __init__(self,op,resolution=.5):
        self.op=op;self.resolution=resolution;self.stock,self.tool,self.commands,self.stamp=snapshot(op,resolution);self.native=PathSimulator.PathSim();self.native.BeginSimulation(self.stock,resolution);self.native.SetToolShape(self.tool,min(.05,resolution/10));self.position=App.Placement(App.Vector(0,0,self.stock.BoundBox.ZMax+1),App.Rotation());self.index=0
    def valid(self):
        if snapshot(self.op,self.resolution)[3]!=self.stamp:raise ValueError('Simulation inputs changed;reopen')
    def step(self):
        self.valid()
        if self.index>=len(self.commands):return False
        self.position=self.native.ApplyCommand(self.position,self.commands[self.index]);self.index+=1;return True
    def meshes(self):
        self.valid();meshes=self.native.GetResultMesh()
        if sum(x.CountFacets for x in meshes)>500000:raise ValueError('Preview mesh exceeds limit')
        return meshes
