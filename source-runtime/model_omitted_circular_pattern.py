"""Guarded circular copies with individual instance omission."""
import FreeCAD as App
import Part,model,model_axis
from circular_pattern_values import checked_polar
from path_pattern_suppression_values import checked_instances
from model_reference_pattern import bounded,reference_signature
from model_defeature import containers
from model_point_loft import parents,hierarchy

def checked(doc,source,reference=None,existing=None):
    if existing and not getattr(existing,'FluxCircularOmission',False):raise ValueError('Create a new omitted circular pattern;legacy array cannot change representation')
    for item in [source]+([reference] if reference is not None else []):
        if item is None or item.Document!=doc or doc.getObject(item.Name)!=item or item.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (item==existing or existing in item.OutListRecursive):raise ValueError('Cyclic circular pattern reference')
        if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [item]+list(item.OutListRecursive)):raise ValueError('Repair input errors first')
        if item.Shape.isNull() or not item.Shape.isValid():raise ValueError('Input is empty or invalid')

def shape(source,count=3,axis='Z',angle=360,center=(0,0,0),reverse=False,reference=None,subelement='',suppressed_instances=None):
    from draftobjects.array import polar_placements
    checked(source.Document if source else None,source,reference)
    if type(axis) is str:
        if axis not in ('X','Y','Z'):raise ValueError('Invalid world axis')
        axis={'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]
    # Validate numeric API values even when geometry overrides the axis.
    count,angle,direction,origin=checked_polar(count,angle,axis,center,reverse)
    if reference:
        point,vector,kind=model_axis.validate(source.Document,reference,subelement)
        bounded(model.world_shape(reference))
        count,angle,direction,origin=checked_polar(count,angle,tuple(vector),tuple(point),reverse)
    omitted=checked_instances(suppressed_instances,count)
    base=model.world_shape(source);bounded(base)
    if not base.Solids or base.Volume<=1e-9 or len(base.Solids)*count>2000:raise ValueError('Use solid bodies with at most2000 full-pattern solids')
    shapes=[]
    for pose in polar_placements(App.Placement(),App.Vector(*origin),angle,count,App.Vector(*direction),App.Vector()):
        item=base.copy();item.Placement=pose.multiply(item.Placement);shapes.append(item)
    out=Part.makeCompound(shapes);bounded(out)
    if not out.isValid() or len(out.Solids)!=len(base.Solids)*count:raise ValueError('Invalid full circular pattern')
    if omitted:
        out=Part.makeCompound([item for index,item in enumerate(shapes,1) if index not in omitted])
        if not out.isValid() or len(out.Solids)!=len(base.Solids)*(count-len(omitted)):raise ValueError('Invalid retained circular pattern')
    return out

def settings(obj):
    ref=obj.DirectionSource if obj.UseReference else None
    axis=str(obj.AxisKey) if str(obj.AxisKey) in ('X','Y','Z') else tuple(obj.Axis)
    return dict(kind='circular',count=obj.NumberPolar,axis=axis,angle=obj.Angle.Value,center=tuple(obj.Center),reverse=bool(obj.Reversed),reference=ref,subelement=str(obj.DirectionElement) if ref else '',axis_mode='reference' if obj.UseReference else 'world' if type(axis) is str else 'vector',suppressed_instances=checked_instances(getattr(obj,'SuppressedInstances',()),obj.NumberPolar))

def input_signature(obj):
    refs=[obj.FluxBodySource]+([obj.DirectionSource] if obj.UseReference else [])
    return (tuple((o.Name,reference_signature(o)) if o else None for o in refs),obj.NumberPolar,obj.Angle.Value,tuple(obj.Axis),tuple(obj.Center),str(obj.AxisKey),bool(obj.Reversed),bool(obj.UseReference),str(obj.DirectionElement),tuple(getattr(obj,'SuppressedInstances',())),str(obj.getGlobalPlacement()))

class OmittedCircularPattern:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            if obj.UseReference and obj.DirectionSource is None:raise ValueError('Axis reference is missing')
            inputs=[obj.FluxBodySource]+([obj.DirectionSource] if obj.UseReference else []);checked(obj.Document,inputs[0],inputs[1] if len(inputs)>1 else None,obj)
            if hierarchy(inputs)!=list(obj.SourceHierarchy):raise ValueError('Input hierarchy changed;reselect inputs')
            if obj.UseReference and model_axis.geometry(obj.DirectionSource,obj.DirectionElement)[2]!=obj.AxisGeometryKind:raise ValueError('Axis geometry changed;reselect axis')
            values=settings(obj);values.pop('kind');values.pop('axis_mode');obj.Shape=shape(obj.FluxBodySource,**values);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,source,count=3,axis='Z',angle=360,center=(0,0,0),reverse=False,reference=None,subelement='',existing=None,suppressed_instances=None,reference_mode=None):
    from model_features import placed_preview,verify_result
    if reference_mode is not None and type(reference_mode) is not bool:raise ValueError('Invalid axis reference mode')
    if getattr(existing,'FluxCircularOmission',False) and existing.UseReference and reference is None and reference_mode is not False:reference=existing.DirectionSource;subelement=subelement or existing.DirectionElement
    if reference_mode is True and reference is None:raise ValueError('Select an axis reference')
    if reference_mode is False:reference=None;subelement=''
    checked(doc,source,reference,existing)
    omitted=checked_instances(suppressed_instances,count,getattr(existing,'SuppressedInstances',()))
    out=shape(source,count,axis,angle,center,reverse,reference,subelement,omitted);expected=placed_preview(out,existing)
    axis_key=axis if type(axis) is str else 'vector';direction={'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis] if type(axis) is str else axis
    unused,angle,unit,origin=checked_polar(count,angle,direction,center,False)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Omitted Circular Pattern'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','OmittedCircularPattern')
            for typ,key in [('App::PropertyString','FluxPattern'),('App::PropertyBool','FluxCircularOmission'),('App::PropertyLinkGlobal','Base'),('App::PropertyLinkGlobal','FluxBodySource'),('App::PropertyInteger','NumberPolar'),('App::PropertyAngle','Angle'),('App::PropertyVector','Axis'),('App::PropertyVectorDistance','Center'),('App::PropertyString','AxisKey'),('App::PropertyBool','Reversed'),('App::PropertyBool','UseReference'),('App::PropertyLinkGlobal','DirectionSource'),('App::PropertyString','DirectionElement'),('App::PropertyString','AxisGeometryKind'),('App::PropertyIntegerList','SuppressedInstances'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'Pattern')
            obj.FluxPattern='circular';obj.FluxCircularOmission=True;OmittedCircularPattern(obj);obj.ViewObject.Proxy=0
            for key in ('FluxPattern','FluxCircularOmission','Base','FluxBodySource','AxisKey','Reversed','UseReference','DirectionSource','DirectionElement','AxisGeometryKind','SuppressedInstances','SourceContainers','SourceHierarchy'):obj.setEditorMode(key,2)
            obj.setEditorMode('Error',1)
        obj.Base=source;obj.FluxBodySource=source;obj.NumberPolar=count;obj.Angle=angle;obj.Axis=App.Vector(*unit);obj.Center=App.Vector(*origin);obj.AxisKey=axis_key;obj.Reversed=reverse;obj.UseReference=reference is not None;obj.DirectionSource=reference;obj.DirectionElement=subelement if reference else '';obj.AxisGeometryKind=model_axis.geometry(reference,subelement)[2] if reference else '';obj.SuppressedInstances=list(omitted)
        inputs=[source]+([reference] if reference else []);obj.SourceContainers=parents(inputs);obj.SourceHierarchy=hierarchy(inputs);obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,expected)
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;edit cancelled')
        source.Visibility=False;obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        members=self.previous.pop((changed.Document.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in changed.Document.Objects:
            if getattr(obj,'FluxCircularOmission',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SourceContainers)) for s in (obj.FluxBodySource,obj.DirectionSource if obj.UseReference else None)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_omitted_circular_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_omitted_circular_observer=observer
install_observer()
