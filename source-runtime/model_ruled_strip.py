"""Linked ruled surface strip from one straight boundary edge and adjacent planar face."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from model_construction import element,edge,face
import math
from ruled_strip_values import checked_values
from edge_intersection_bounds import checked_coordinates

def checked(doc,a,b,existing=None):
    for ref in (a,b):
        if type(ref) not in (tuple,list) or len(ref)!=2:raise ValueError('Select one explicit edge and adjacent face.')
        source=ref[0]
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select sources in the current document.')
        if source.isDerivedFrom('App::Link'):raise ValueError('Links are excluded.')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic surface reference.')
        if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if a[0]!=b[0]:raise ValueError('Select an edge and its adjacent face on the same source.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxRuledStrip',False)):raise ValueError('Select a ruled strip to edit.')

def preview(doc,a,b,distance=10.,angle=0.,mode='normal',reverse=False,existing=None,direction_reference=None,direction_element=''):
    if mode=='direction':
        if type(mode) is not str:raise ValueError('Invalid direction mode')
        from ruled_direction_geometry import build
        checked(doc,a,b,existing);out=build(doc,a,b,direction_reference,direction_element,distance,angle,reverse,existing)
        if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
        return out
    checked(doc,a,b,existing);distance,angle,mode,reverse=checked_values(distance,angle,mode,reverse)
    curve=element(a,'Edge')
    if isinstance(curve.Curve,Part.Circle):
        from circular_ruled_geometry import build
        center,normal=face(b);out=build(curve,element(b,'Face'),distance,angle,mode,reverse)
        if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
        return out
    origin,tangent=edge(a);center,normal=face(b);surface=element(b,'Face')
    if not any(abs(curve.common(boundary).Length-curve.Length)<=max(1e-7,curve.Length*1e-9) and abs(boundary.Length-curve.Length)<=max(1e-7,curve.Length*1e-9) for boundary in surface.Edges):raise ValueError('Select a complete boundary edge of the planar face.')
    co=normal.cross(tangent);co.normalize();theta=math.radians(angle)
    direction=(normal*math.cos(theta)+co*math.sin(theta)) if mode=='normal' else (co*math.cos(theta)+normal*math.sin(theta))
    if reverse:direction=-direction
    shift=direction*distance
    for vertex in curve.Vertexes:
        checked_coordinates(tuple(vertex.Point));checked_coordinates(tuple(vertex.Point+shift))
    second=curve.copy();second.translate(shift);out=Part.makeRuledSurface(curve,second)
    if out.isNull() or not out.isValid() or len(out.Faces)!=1 or out.Solids or abs(out.Area-curve.Length*distance)>max(1e-7,curve.Length*distance*1e-8):raise ValueError('Cannot make a valid ruled strip.')
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

class RuledStrip:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            if containers(obj.SourceA)!=list(obj.ContainersA) or containers(obj.SourceB)!=list(obj.ContainersB):raise ValueError('Source hierarchy changed; reselect edges.')
            if obj.DirectionMode=='direction' and containers(getattr(obj,'DirectionSource',None))!=list(getattr(obj,'ContainersC',[])):raise ValueError('Direction hierarchy changed;reselect direction')
            out=preview(obj.Document,(obj.SourceA,obj.EdgeA),(obj.SourceB,obj.FaceB),obj.Distance.Value,obj.Angle.Value,obj.DirectionMode,obj.Reverse,direction_reference=getattr(obj,'DirectionSource',None) if obj.DirectionMode=='direction' else None,direction_element=str(getattr(obj,'DirectionElement','')));obj.Shape=Part.makeCompound([out]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,a,b,distance=None,angle=None,mode=None,reverse=None,existing=None,direction_reference=None,direction_element=''):
    distance=existing.Distance.Value if distance is None and existing else (10. if distance is None else distance)
    angle=existing.Angle.Value if angle is None and existing else (0. if angle is None else angle)
    mode=existing.DirectionMode if mode is None and existing else ('normal' if mode is None else mode)
    reverse=existing.Reverse if reverse is None and existing else (False if reverse is None else reverse)
    if mode=='direction':
        if type(mode) is not str:raise ValueError('Invalid direction mode')
        if direction_reference is None and existing:direction_reference=getattr(existing,'DirectionSource',None);direction_element=direction_element or str(getattr(existing,'DirectionElement',''))
    else:
        distance,angle,mode,reverse=checked_values(distance,angle,mode,reverse)
        if direction_reference is not None:raise ValueError('Use direction mode with a direction reference')
    expected=preview(doc,a,b,distance,angle,mode,reverse,existing,direction_reference,direction_element)
    downstream={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Ruled Surface From Edge'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','RuledStrip')
            for typ,key in [('App::PropertyBool','FluxRuledStrip'),('App::PropertyLinkGlobal','SourceA'),('App::PropertyLinkGlobal','SourceB'),('App::PropertyLinkListGlobal','ContainersA'),('App::PropertyLinkListGlobal','ContainersB'),('App::PropertyString','EdgeA'),('App::PropertyString','FaceB'),('App::PropertyLength','Distance'),('App::PropertyAngle','Angle'),('App::PropertyString','DirectionMode'),('App::PropertyBool','Reverse'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxRuledStrip=True;RuledStrip(obj);obj.ViewObject.Proxy=0;obj.ViewObject.ShapeColor=(1.,.65,.25)
            for key in ('FluxRuledStrip','ContainersA','ContainersB'):obj.setEditorMode(key,2)
            for key in ('SourceA','SourceB','EdgeA','FaceB','Distance','Angle','DirectionMode','Reverse','Error'):obj.setEditorMode(key,1)
        if mode=='direction' and 'DirectionSource' not in obj.PropertiesList:
            obj.addProperty('App::PropertyLinkGlobal','DirectionSource','FluxCAD');obj.addProperty('App::PropertyString','DirectionElement','FluxCAD');obj.addProperty('App::PropertyLinkListGlobal','ContainersC','FluxCAD')
            for key in ('DirectionSource','DirectionElement'):obj.setEditorMode(key,1)
            obj.setEditorMode('ContainersC',2)
        if 'DirectionSource' in obj.PropertiesList:
            obj.DirectionSource=direction_reference if mode=='direction' else None;obj.DirectionElement=direction_element if mode=='direction' else '';obj.ContainersC=containers(direction_reference) if mode=='direction' else []
        obj.Distance=distance;obj.Angle=angle;obj.DirectionMode=mode;obj.Reverse=reverse;obj.SourceA=a[0];obj.EdgeA=a[1];obj.SourceB=b[0];obj.FaceB=b[1];obj.ContainersA=containers(a[0]);obj.ContainersB=containers(b[0]);obj.touch();doc.recompute();out=model.world_shape(obj)
        if obj.Error or out.isNull() or len(out.Faces)!=1 or abs(out.Area-expected.Area)>max(1e-7,expected.Area*1e-9) or abs(out.common(expected).Area-expected.Area)>max(1e-7,expected.Area*1e-9):raise ValueError(obj.Error or 'Preview and result differ.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not now for was,now in zip(downstream[child.Name],(bool(child.Shape.Solids),bool(child.Shape.Faces),bool(child.Shape.Edges))))))):raise ValueError('Later feature invalid; edit cancelled.')
        obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxRuledStrip',False):
                for source,key in ((obj.SourceA,'ContainersA'),(obj.SourceB,'ContainersB'),(getattr(obj,'DirectionSource',None),'ContainersC')):
                    if source and (source.Name in members or changed in containers(source) or changed in list(getattr(obj,key))):obj.touch();break
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_ruled_strip_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_ruled_strip_observer=observer
install_observer()
