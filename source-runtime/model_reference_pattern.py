"""Rectangular pattern with a guarded original straight-edge direction."""
import math,re
from rectangular_suppression_values import checked_cells,parse_cells,format_cells
import FreeCAD as App
import Part
import model
from model_defeature import containers
from model_point_loft import parents,hierarchy
from rectangular_direction_values import checked_direction
from rectangular_second_direction import independent_directions,resolve_second_mode

def checked(doc,source,reference,existing=None,reference2=None):
    if existing and not getattr(existing,'FluxReferencePattern',False):raise ValueError('Create a new reference-direction pattern;native array cannot change representation')
    for item in [source,reference]+([reference2] if reference2 is not None else []):
        if item is None or item.Document!=doc or doc.getObject(item.Name)!=item or item.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (item==existing or existing in item.OutListRecursive):raise ValueError('Cyclic pattern reference')
        if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [item]+list(item.OutListRecursive)):raise ValueError('Repair input errors first')
        if item.Shape.isNull() or not item.Shape.isValid():raise ValueError('Input shape is empty or invalid')

def bounded(shape):
    box=shape.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)):raise ValueError('Pattern bounds exceed +/-1000000mm')

def reference_signature(reference):
    return (None if reference.Shape.isNull() else reference.Shape.hashCode(),str(reference.getGlobalPlacement()),tuple(hierarchy([reference])),tuple((o.Name,tuple(o.State),str(getattr(o,'Error',''))) for o in [reference]+list(reference.OutListRecursive)))

def direction(reference,subelement):
    if type(subelement) is not str or not re.fullmatch(r'Edge[1-9][0-9]*',subelement):raise ValueError('Select an explicit straight EdgeN')
    try:edge=model.world_shape(reference).getElement(subelement)
    except (IndexError,Part.OCCError):raise ValueError('Referenced edge is missing;reselect the direction') from None
    if edge.ShapeType!='Edge' or not isinstance(edge.Curve,Part.Line) or not 1e-7<edge.Length<=1e7:raise ValueError('Use a straight edge of length >1e-7..10000000mm')
    bounded(edge)
    return App.Vector(*checked_direction(tuple(edge.tangentAt(edge.FirstParameter))))

def shape(source,reference,subelement,count=3,spacing=10,count2=1,axis2='Y',spacing2=10,distribution='spacing',reference2=None,subelement2='',reference_mode2=None,suppressed_cells=None):
    from model_features import rectangular_intervals
    from draftobjects.array import rect_placements
    enabled=resolve_second_mode(reference_mode2,reference2 is not None)
    if enabled and (reference2 is None or type(count2) is not int or count2<=1):raise ValueError('Second reference requires a reference and quantity2 greater than1')
    checked(source.Document if source else None,source,reference,reference2=reference2 if enabled else None)
    if type(count) is not int or type(count2) is not int or type(axis2) is not str or axis2 not in ('X','Y','Z'):raise ValueError('Invalid pattern quantities or second axis')
    for value in (spacing,spacing2):
        if type(value) not in (int,float):raise ValueError('Invalid pattern distance')
        try:finite=math.isfinite(value)
        except (ValueError,OverflowError):finite=False
        if not finite:raise ValueError('Pattern distance must be finite')
    # Reuse the existing quantity,distance and distribution contract.
    first,second=rectangular_intervals(count,'X',spacing,count2,'Y',spacing2,distribution)
    unit=direction(reference,subelement);first=unit*first.x
    if enabled:
        unused,unit2=independent_directions(tuple(unit),tuple(direction(reference2,subelement2)))
        second=App.Vector(*unit2)*second.y
    else:second=App.Vector(*{'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis2])*second.y
    if count2>1 and unit.cross(second/second.Length).Length<1e-7:raise ValueError('Pattern directions must be nonparallel')
    base=model.world_shape(source);bounded(base)
    if not base.Solids or base.Volume<=1e-9 or len(base.Solids)*count*count2>2000:raise ValueError('Use a solid body and at most2000 resulting solids')
    omitted=checked_cells(() if suppressed_cells is None else suppressed_cells,count,count2)
    result=[]
    for pose in rect_placements(App.Placement(),first,second,App.Vector(),count,count2,1):
        item=base.copy();item.Placement=pose.multiply(item.Placement);result.append(item)
    out=Part.makeCompound(result);bounded(out)
    if not out.isValid() or len(out.Solids)!=len(base.Solids)*count*count2:raise ValueError('Invalid pattern result')
    if omitted:
        out=Part.makeCompound([item for k,item in enumerate(result) if (k//count2+1,k%count2+1) not in omitted])
        if not out.isValid() or len(out.Solids)!=len(base.Solids)*(count*count2-len(omitted)):raise ValueError("Invalid suppressed pattern result")
    return out

def settings(obj):
    return dict(axis='X',reference=obj.DirectionSource,subelement=obj.DirectionElement,reference_mode=True,axis_mode='reference',count=obj.NumberX,count2=obj.NumberY,spacing=obj.FluxDistance1.Value,spacing2=obj.FluxDistance2.Value,axis2=str(obj.SecondAxis),distribution=str(obj.FluxDistribution),angle=360,center=(0,0,0),reverse=False,kind='linear',reference2=getattr(obj,'DirectionSource2',None),subelement2=str(getattr(obj,'DirectionElement2','')),reference_mode2=bool(getattr(obj,'UseDirection2Reference',False)),suppressed_cells=parse_cells(','.join(getattr(obj,'SuppressedCells',[])),obj.NumberX,obj.NumberY))

class ReferencePattern:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            values=settings(obj)
            if values['reference_mode2'] and values['reference2'] is None:raise ValueError('Second reference is missing;reselect direction2')
            inputs=[obj.FluxBodySource,obj.DirectionSource]+([values['reference2']] if values['reference_mode2'] else []);checked(obj.Document,inputs[0],inputs[1],obj,reference2=values['reference2'] if values['reference_mode2'] else None)
            if hierarchy(inputs)!=list(obj.SourceHierarchy):raise ValueError('Source hierarchy changed;reselect inputs')
            out=shape(inputs[0],inputs[1],obj.DirectionElement,values['count'],values['spacing'],values['count2'],values['axis2'],values['spacing2'],values['distribution'],values['reference2'],values['subelement2'],values['reference_mode2'],values['suppressed_cells'])
            obj.Shape=out;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,source,reference,subelement,count=3,spacing=10,count2=1,axis2='Y',spacing2=10,distribution='spacing',existing=None,reference2=None,subelement2='',reference_mode2=None,suppressed_cells=None):
    from model_features import placed_preview,verify_result
    enabled=resolve_second_mode(reference_mode2,bool(getattr(existing,'UseDirection2Reference',False)) or reference2 is not None)
    if enabled:
        reference2=reference2 if reference2 is not None else getattr(existing,'DirectionSource2',None)
        subelement2=subelement2 or str(getattr(existing,'DirectionElement2',''))
    else:reference2=None;subelement2=''
    if suppressed_cells is None:suppressed_cells=parse_cells(','.join(getattr(existing,'SuppressedCells',[])),count,count2)
    suppressed_cells=checked_cells(suppressed_cells,count,count2)
    checked(doc,source,reference,existing,reference2);expected=placed_preview(shape(source,reference,subelement,count,spacing,count2,axis2,spacing2,distribution,reference2,subelement2,enabled,suppressed_cells),existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Reference Direction Pattern'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','ReferencePattern')
            for typ,key in [('App::PropertyBool','FluxReferencePattern'),('App::PropertyString','FluxPattern'),('App::PropertyLinkGlobal','Base'),('App::PropertyLinkGlobal','FluxBodySource'),('App::PropertyLinkGlobal','DirectionSource'),('App::PropertyString','DirectionElement'),('App::PropertyInteger','NumberX'),('App::PropertyInteger','NumberY'),('App::PropertyEnumeration','SecondAxis'),('App::PropertyEnumeration','FluxDistribution'),('App::PropertyDistance','FluxDistance1'),('App::PropertyDistance','FluxDistance2'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'Pattern')
            obj.FluxReferencePattern=True;obj.FluxPattern='linear';obj.SecondAxis=['X','Y','Z'];obj.FluxDistribution=['spacing','extent'];ReferencePattern(obj);obj.ViewObject.Proxy=0
            for key in ('FluxReferencePattern','FluxPattern','Base','FluxBodySource','DirectionSource','DirectionElement','SourceContainers','SourceHierarchy'):obj.setEditorMode(key,2)
            obj.setEditorMode('Error',1)
        for typ,key in [('App::PropertyBool','UseDirection2Reference'),('App::PropertyLinkGlobal','DirectionSource2'),('App::PropertyString','DirectionElement2')]:
            if key not in obj.PropertiesList:obj.addProperty(typ,key,'Pattern');obj.setEditorMode(key,2)
        if 'SuppressedCells' not in obj.PropertiesList:obj.addProperty('App::PropertyStringList','SuppressedCells','Pattern');obj.setEditorMode('SuppressedCells',2)
        obj.SuppressedCells=[f'{col}:{row}' for col,row in suppressed_cells]
        obj.UseDirection2Reference=enabled;obj.DirectionSource2=reference2;obj.DirectionElement2=subelement2
        inputs=[source,reference]+([reference2] if enabled else [])
        obj.Base=source;obj.FluxBodySource=source;obj.DirectionSource=reference;obj.DirectionElement=subelement;obj.SourceContainers=parents(inputs);obj.SourceHierarchy=hierarchy(inputs);obj.NumberX=count;obj.NumberY=count2;obj.SecondAxis=axis2;obj.FluxDistribution=distribution;obj.FluxDistance1=spacing;obj.FluxDistance2=spacing2;obj.touch();doc.recompute()
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
            if getattr(obj,'FluxReferencePattern',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SourceContainers)) for s in (obj.FluxBodySource,obj.DirectionSource,getattr(obj,'DirectionSource2',None))):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_reference_pattern_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_reference_pattern_observer=observer
install_observer()
