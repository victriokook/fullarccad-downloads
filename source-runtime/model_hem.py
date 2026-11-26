"""Guarded single-edge hems using the bundled SheetMetal bending kernel.

Flat/Open/closed Teardrop/closed Rolled; fixed MaterialOutside, no relief,
gaps, miter, open-roll controls or manufacturing certification.
"""
import math,re
import FreeCAD as App,Part
import model,sheetmetal_bridge
from model_point_loft import parents,hierarchy
from model_defeature import containers
from hem_values import validate

def bounded(shape):
    b=shape.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)):raise ValueError('Hem bounds exceed +/-1000000mm')

def checked(source,edge,existing=None):
    doc=App.ActiveDocument
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select a current-document non-Link sheet solid')
    if existing and (not getattr(existing,'FluxHem',False) or source==existing or existing in source.OutListRecursive):raise ValueError('Invalid or cyclic hem reference')
    if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [source]+list(source.OutListRecursive)):raise ValueError('Repair source errors first')
    if not hasattr(source,'Shape') or source.Shape.isNull() or not source.Shape.isValid() or len(source.Shape.Solids)!=1 or len(source.Shape.Edges)>200:raise ValueError('Use one valid sheet solid with at most200 edges')
    if type(edge) is not str or not re.fullmatch(r'Edge[1-9][0-9]*',edge):raise ValueError('Select one explicit straight EdgeN')
    shape=model.world_shape(source);bounded(shape)
    try:e=shape.getElement(edge)
    except (IndexError,Part.OCCError):raise ValueError('Hem edge is missing;reselect it') from None
    if not isinstance(e.Curve,Part.Line) or e.Length<=1e-7:raise ValueError('Hem requires a straight boundary edge')
    return shape

def shape(source,edge,kind='Open',width=10.,opening=1.,radius=1.,include_bend=True,invert=False,unfold=False):
    sheetmetal_bridge.unavailable()

def settings(obj):
    return dict(kind=str(obj.HemType),width=obj.Width.Value,opening=obj.Opening.Value,radius=obj.Radius.Value,include_bend=obj.IncludeBend,invert=obj.Reverse)

def signature(source,edge,existing=None):
    checked(source,edge,existing)
    if existing is not None and existing.ExpressionEngine:raise ValueError('Hem expressions cannot be overwritten;edit the expression in Properties')
    def stamp(o):return (o.Name,o.Shape.hashCode(),str(o.getGlobalPlacement()),tuple(o.State),str(getattr(o,'Error','')))
    return (tuple(stamp(o) for o in [source]+list(source.OutListRecursive) if hasattr(o,'Shape')),tuple(hierarchy([source])),edge,None if existing is None else (stamp(existing),tuple(settings(existing).items()),existing.Edge,tuple(existing.SourceHierarchy)))

class Hem:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Source,obj.Edge,obj)
            if hierarchy([obj.Source])!=list(obj.SourceHierarchy):raise ValueError('Source hierarchy changed;reselect the hem edge')
            out=shape(obj.Source,obj.Edge,**settings(obj));obj.Shape=out;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

class ViewProvider:
    def __init__(self,vo):vo.Proxy=self
    def doubleClicked(self,vo):
        import FreeCADGui as Gui,hem_ui
        hem_ui.show(Gui.fluxcad_workspace,vo.Object);return True
    def dumps(self):return None
    def loads(self,state):pass

def apply(source,edge,kind='Open',width=10.,opening=1.,radius=1.,include_bend=True,invert=False,existing=None,expected=None):
    checked(source,edge,existing)
    if existing is not None and existing.ExpressionEngine:raise ValueError('Hem expressions cannot be overwritten;edit the expression in Properties')
    if expected is not None and signature(source,edge,existing)!=expected:raise ValueError('Inputs changed;close and reopen')
    from model_features import placed_preview,verify_result
    preview=placed_preview(shape(source,edge,kind,width,opening,radius,include_bend,invert),existing)
    doc=source.Document;downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Hem'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','Hem')
            for typ,n in [('App::PropertyBool','FluxHem'),('App::PropertyLinkGlobal','Source'),('App::PropertyString','Edge'),('App::PropertyEnumeration','HemType'),('App::PropertyLength','Width'),('App::PropertyLength','Opening'),('App::PropertyLength','Radius'),('App::PropertyBool','IncludeBend'),('App::PropertyBool','Reverse'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,n,'Hem')
            obj.FluxHem=True;obj.HemType=['Flat','Open','Teardrop','Rolled'];Hem(obj);ViewProvider(obj.ViewObject)
            for n in ('FluxHem','Source','Edge','SourceContainers','SourceHierarchy'):obj.setEditorMode(n,2)
            obj.setEditorMode('Error',1)
        obj.Source=source;obj.Edge=edge;obj.SourceContainers=parents([source]);obj.SourceHierarchy=hierarchy([source]);obj.HemType=kind;obj.Width=width;obj.Opening=opening;obj.Radius=radius;obj.IncludeBend=include_bend;obj.Reverse=invert;obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,preview)
        for child in obj.InListRecursive:
            if getattr(child,'Error','') or 'Invalid' in child.State or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;hem edit cancelled')
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
            if getattr(obj,'FluxHem',False) and obj.Source and (obj.Source.Name in members or changed in containers(obj.Source) or changed in list(obj.SourceContainers)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}

old=getattr(App,'_fullarc_hem_observer',None)
if old is not None:App.removeDocumentObserver(old)
App._fullarc_hem_observer=HierarchyObserver();App.addDocumentObserver(App._fullarc_hem_observer)
