"""Direct-source, fail-closed histories for four bounded native operations."""
import importlib,json,math,re
import FreeCAD as App,Part
import model
from model_point_loft import parents,hierarchy
from model_defeature import containers
MODULES={'fixed':'fixed_sweep_op','fold':'fold_line_op','relief':'corner_relief_op','junction':'junction_op'}
def module(kind):
    if type(kind) is not str or kind not in MODULES:raise ValueError('Unknown operation')
    return importlib.import_module(MODULES[kind])
def bounded(shape):
    box=shape.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)):raise ValueError('Coordinates exceed +/-1000000mm')
def element(shape,name,prefix):
    if type(name) is not str or not re.fullmatch(prefix+'[1-9][0-9]*',name):raise ValueError('Select explicit '+prefix+'N')
    try:return shape.getElement(name)
    except (IndexError,Part.OCCError):raise ValueError('Missing '+prefix+';reselect input') from None
def checked(kind,sources,elements,options,existing=None):
    module(kind)
    if type(sources) not in (list,tuple) or not sources or len(set(sources))!=len(sources):raise ValueError('Select different live inputs')
    doc=sources[0].Document if sources[0] else None
    if doc is None:raise ValueError('No source document')
    if existing and (existing.Document!=doc or doc.getObject(existing.Name)!=existing or not getattr(existing,'FluxFourOp',False) or existing.Operation!=kind):raise ValueError('Edit the same operation in the source document')
    for source in sources:
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic operation reference')
        if any('Invalid' in x.State or 'Error' in x.State or getattr(x,'Error','') for x in [source]+list(source.OutListRecursive)):raise ValueError('Repair input errors first')
        if not hasattr(source,'Shape') or source.Shape.isNull() or not source.Shape.isValid() or len(source.Shape.Edges)>200:raise ValueError('Use valid inputs with at most200 edges')
        bounded(model.world_shape(source))
    if type(elements) not in (list,tuple) or any(type(x) is not str for x in elements) or type(options) is not dict:raise ValueError('Invalid settings')
def shape(kind,sources,elements,options):
    checked(kind,sources,elements,options)
    try:out=module(kind).shape(sources,elements,options)
    except (Part.OCCError,RuntimeError,IndexError,UnboundLocalError) as error:raise ValueError('Native operation failed: '+str(error)) from None
    if out is None or out.isNull() or not out.isValid() or len(out.Solids)!=1 or not math.isfinite(out.Volume) or out.Volume<=1e-9:raise ValueError('Operation must produce one valid solid')
    bounded(out);return Part.makeCompound([out])
def settings(obj):return json.loads(obj.SettingsJSON)
def signature(kind,sources,elements,options,existing=None):
    checked(kind,sources,elements,options,existing)
    def stamp(s):return (s.Name,s.Shape.hashCode(),str(s.getGlobalPlacement()),tuple(s.State),str(getattr(s,'Error','')))
    return (tuple(stamp(s) for s in sources),tuple(hierarchy(sources)),tuple((x.Name,tuple(x.State),str(getattr(x,'Error',''))) for s in sources for x in s.OutListRecursive),tuple(elements),None if not existing else (stamp(existing),existing.Operation,existing.SettingsJSON,tuple(x.Name for x in existing.InputObjects),tuple(existing.Elements),tuple(existing.InputHierarchy)))
class Operation:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            sources=list(obj.InputObjects);options=settings(obj);checked(obj.Operation,sources,list(obj.Elements),options,obj)
            if hierarchy(sources)!=list(obj.InputHierarchy):raise ValueError('Input hierarchy changed;reselect inputs')
            obj.Shape=shape(obj.Operation,sources,list(obj.Elements),options);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass
class ViewProvider:
    def __init__(self,vo):vo.Proxy=self
    def doubleClicked(self,vo):
        import FreeCADGui as Gui,four_ops_ui
        four_ops_ui.show(Gui.fluxcad_workspace,vo.Object.Operation,vo.Object);return True
    def dumps(self):return None
    def loads(self,state):pass
def apply(kind,sources,elements,options,existing=None,expected=None):
    checked(kind,sources,elements,options,existing)
    if expected is not None and signature(kind,sources,elements,options,existing)!=expected:raise ValueError('Inputs changed;close and reopen')
    from model_features import placed_preview,verify_result
    preview=placed_preview(shape(kind,sources,elements,options),existing);doc=sources[0].Document
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    encoded=json.dumps(options,sort_keys=True,allow_nan=False)
    with model.transaction(doc,module(kind).TITLE[1]):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','FullArcOperation')
            for typ,key in [('App::PropertyBool','FluxFourOp'),('App::PropertyString','Operation'),('App::PropertyLinkListGlobal','InputObjects'),('App::PropertyStringList','Elements'),('App::PropertyString','SettingsJSON'),('App::PropertyLinkListGlobal','InputContainers'),('App::PropertyStringList','InputHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FullArcCAD')
            obj.FluxFourOp=True;obj.Operation=kind;obj.Label=module(kind).TITLE[1];Operation(obj);ViewProvider(obj.ViewObject)
            for key in ('FluxFourOp','Operation','InputObjects','Elements','InputContainers','InputHierarchy'):obj.setEditorMode(key,2)
            obj.setEditorMode('Error',1);obj.setEditorMode('SettingsJSON',1)
        obj.InputObjects=list(sources);obj.Elements=list(elements);obj.SettingsJSON=encoded;obj.InputContainers=parents(sources);obj.InputHierarchy=hierarchy(sources);obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,preview)
        for child in obj.InListRecursive:
            if getattr(child,'Error','') or 'Invalid' in child.State or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;edit cancelled')
        for source in sources:source.Visibility=False
        obj.Visibility=True
    return obj
class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,o,prop):
        if prop=='Group' and o.TypeId in ('App::Part','PartDesign::Body') and o.Document:self.previous[(o.Document.Name,o.Name)]={x.Name for x in o.Group}
    def slotChangedObject(self,o,prop):
        if prop!='Group' or o.TypeId not in ('App::Part','PartDesign::Body') or not o.Document:return
        members=self.previous.pop((o.Document.Name,o.Name),set())|{x.Name for x in o.Group}
        for q in o.Document.Objects:
            if getattr(q,'FluxFourOp',False) and any(s and (s.Name in members or o in containers(s) or o in list(q.InputContainers)) for s in q.InputObjects):q.touch()
    def slotDeletedDocument(self,d):self.previous={k:v for k,v in self.previous.items() if k[0]!=d.Name}
old=getattr(App,'_fullarc_four_observer',None)
if old is not None:App.removeDocumentObserver(old)
App._fullarc_four_observer=HierarchyObserver();App.addDocumentObserver(App._fullarc_four_observer)
