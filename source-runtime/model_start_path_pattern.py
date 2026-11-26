"""Guarded original-input path pattern with an arc-length start fraction."""
import math
import FreeCAD as App
import Part
import model
import model_path_pattern as legacy
from model_defeature import containers
from model_point_loft import parents,hierarchy
from model_partial_sweep import bounded as bounded_wire
from model_reference_pattern import bounded,reference_signature
from path_pattern_start_values import checked_start,remaining_length
from closed_path_start_values import closed_positions
from path_pattern_suppression_values import checked_instances

def checked(doc,source,path,existing=None):
    if existing and not getattr(existing,'FluxStartPathPattern',False):raise ValueError('Create a new start-position pattern;legacy pattern cannot change representation')
    if source==path:raise ValueError('Select different body and path')
    for item in (source,path):
        if item is None or item.Document!=doc or doc.getObject(item.Name)!=item or item.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (item==existing or existing in item.OutListRecursive):raise ValueError('Cyclic path pattern reference')
        if any('Invalid' in x.State or 'Error' in x.State or getattr(x,'Error','') for x in [item]+list(item.OutListRecursive)):raise ValueError('Repair input errors first')
        if item.Shape.isNull() or not item.Shape.isValid():raise ValueError('Input is empty or invalid')

def settings(obj):
    return dict(count=obj.Count,mode=str(obj.Distribution),distance=obj.Distance.Value,orientation=str(obj.Orientation),reverse=obj.Reverse,start_fraction=checked_start(obj.StartFraction),suppressed_instances=checked_instances(getattr(obj,"SuppressedInstances",()),obj.Count))

def transport(curve,positions,orientation,reverse):
    if orientation=='fixed':return legacy.placements(curve,positions,orientation,reverse)
    origin,initial=curve.at(0,reverse);end=positions[-1];events=set(positions);steps=max(1,int(math.ceil(end/curve.length*128)));events.update(end*i/steps for i in range(steps+1));epsilon=max(1e-8,curve.length*1e-10)
    for boundary in curve.ends[:-1]:
        s=curve.length-boundary if reverse else boundary;events.update(v for v in (s-epsilon,s,s+epsilon) if 0<v<end)
    rotation=App.Rotation();previous=initial;frames={};up=App.Vector(0,0,1) if abs(initial.z)<.9 else App.Vector(0,1,0);up-=initial*up.dot(initial);up.normalize()
    for s in sorted(events):
        point,tangent=curve.at(s,reverse);dot=previous.dot(tangent)
        if dot>1-1e-12:delta=App.Rotation()
        elif dot<-1+1e-9:delta=App.Rotation(rotation.multVec(up),180)
        else:delta=App.Rotation(previous,tangent)
        rotation=delta.multiply(rotation);previous=tangent
        if s in positions:frames[s]=App.Placement(point-rotation.multVec(origin),rotation)
    return [frames[s] for s in positions]

class Cycle:
    def __init__(self,curve,reverse):
        self.curve=curve;self.length=curve.length
        self.ends=list(curve.ends)+[v+(-self.length if reverse else self.length) for v in curve.ends]+[3*self.length]
    def at(self,distance,reverse=False):
        if not math.isfinite(distance) or distance<0 or distance>2*self.length:raise ValueError('Closed path distance out of range')
        wrapped=distance%self.length;tolerance=max(1e-8,self.length*1e-10)
        if wrapped<tolerance or self.length-wrapped<tolerance:wrapped=0
        return self.curve.at(wrapped,reverse)

def build(source,path,count=4,mode='full',distance=10,orientation='fixed',reverse=False,start_fraction=0,suppressed_instances=None):
    checked(source.Document if source else None,source,path)
    if type(count) is not int or type(reverse) is not bool or type(mode) is not str or type(orientation) is not str or type(distance) not in (int,float):raise ValueError('Invalid pattern settings')
    try:p=legacy.validate(count,mode,distance,orientation,reverse)
    except (OverflowError,TypeError):raise ValueError('Invalid pattern settings') from None
    omitted=checked_instances(suppressed_instances,count);fraction=checked_start(start_fraction);curve=legacy.Path(path);bounded_wire(curve.wire)
    if curve.closed:
        positions,extent=closed_positions(curve.length,fraction,count,mode,distance);traversal=Cycle(curve,reverse)
    else:
        left=remaining_length(curve.length,fraction);start=curve.length*fraction
        if left<=1e-7:raise ValueError('Start leaves no usable path')
        extent=left if mode=='full' else distance*(count-1) if mode=='spacing' else distance
        if extent>left+max(1e-7,curve.length*1e-9):raise ValueError('Pattern extent exceeds remaining path')
        extent=min(extent,left)
        if extent/(count-1)<=1e-7:raise ValueError('Pattern interval is too small')
        positions=[start+extent*i/(count-1) for i in range(count)];traversal=curve
    frames=transport(traversal,positions,orientation,reverse);inverse=frames[0].inverse();poses=[f.multiply(inverse) for f in frames]
    base=model.world_shape(source);bounded(base)
    if not base.Solids or base.Volume<=1e-9 or len(base.Solids)*count>2000:raise ValueError('Use a solid body and at most2000 resulting solids')
    shapes=[]
    for i,pose in enumerate(poses):
        if any(not math.isfinite(v) for v in (*pose.Base,*pose.Rotation.Q)):raise ValueError('Undefined path frame')
        item=base.copy()
        if i:item.Placement=pose.multiply(item.Placement)
        shapes.append(item)
    out=Part.makeCompound(shapes);bounded(out)
    if not out.isValid() or len(out.Solids)!=len(base.Solids)*count:raise ValueError('Invalid pattern result')
    if omitted:
        out=Part.makeCompound([item for index,item in enumerate(shapes,1) if index not in omitted]);bounded(out)
        if not out.isValid() or len(out.Solids)!=len(base.Solids)*(count-len(omitted)):raise ValueError("Invalid retained pattern result")
    return out,curve.length,extent

class StartPathPattern:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            inputs=[obj.FluxBodySource,obj.FluxPath];checked(obj.Document,*inputs,obj)
            if hierarchy(inputs)!=list(obj.SourceHierarchy):raise ValueError('Input hierarchy changed;reselect inputs')
            out,length,extent=build(*inputs,**settings(obj));obj.Shape=out;obj.Placement=pose;obj.PathLength=length;obj.Extent=extent;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.PathLength=0;obj.Extent=0;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,source,path,existing=None,start_fraction=None,suppressed_instances=None,**values):
    from model_features import placed_preview,verify_result
    checked(doc,source,path,existing);fraction=checked_start(start_fraction,float(existing.StartFraction) if existing else 0);omitted=checked_instances(suppressed_instances,values.get("count",4),getattr(existing,"SuppressedInstances",()));values=dict(values,start_fraction=fraction,suppressed_instances=omitted);out,_,_=build(source,path,**values);expected=placed_preview(out,existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Start Position Path Pattern'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','StartPathPattern')
            for typ,key in [('App::PropertyBool','FluxPathPattern'),('App::PropertyBool','FluxStartPathPattern'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','FluxBodySource'),('App::PropertyLinkGlobal','Path'),('App::PropertyLinkGlobal','FluxPath'),('App::PropertyInteger','Count'),('App::PropertyEnumeration','Distribution'),('App::PropertyLength','Distance'),('App::PropertyEnumeration','Orientation'),('App::PropertyBool','Reverse'),('App::PropertyFloat','StartFraction'),('App::PropertyLength','PathLength'),('App::PropertyLength','Extent'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'Pattern')
            obj.FluxPathPattern=True;obj.FluxStartPathPattern=True;obj.Distribution=['full','spacing','extent'];obj.Orientation=['fixed','tangent'];StartPathPattern(obj);obj.ViewObject.Proxy=0
            for key in ('FluxPathPattern','FluxStartPathPattern','Source','FluxBodySource','Path','FluxPath','SourceContainers','SourceHierarchy'):obj.setEditorMode(key,2)
            for key in ('PathLength','Extent','Error'):obj.setEditorMode(key,1)
        if "SuppressedInstances" not in obj.PropertiesList:obj.addProperty("App::PropertyIntegerList","SuppressedInstances","Pattern");obj.setEditorMode("SuppressedInstances",2)
        obj.SuppressedInstances=list(omitted)
        obj.Source=source;obj.FluxBodySource=source;obj.Path=path;obj.FluxPath=path;obj.SourceContainers=parents([source,path]);obj.SourceHierarchy=hierarchy([source,path]);obj.Count=values.get('count',4);obj.Distribution=values.get('mode','full');obj.Distance=values.get('distance',10);obj.Orientation=values.get('orientation','fixed');obj.Reverse=values.get('reverse',False);obj.StartFraction=fraction;obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,expected)
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;edit cancelled')
        source.Visibility=False;path.Visibility=False;obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        members=self.previous.pop((changed.Document.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in changed.Document.Objects:
            if getattr(obj,'FluxStartPathPattern',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SourceContainers)) for s in (obj.FluxBodySource,obj.FluxPath)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}
def install_observer():
    old=getattr(App,'_flux_start_path_pattern_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_start_path_pattern_observer=observer
install_observer()
