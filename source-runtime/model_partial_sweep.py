"""Guarded native profile sweep of an arc-length path prefix."""
import math
import FreeCAD as App
import Part
import model
from model_defeature import containers
from model_point_loft import parents,hierarchy
from sweep_fraction_values import resolve_fraction
from pipe_path_prefix import prefix
from pipe_path_span import span
from sweep_backward_values import resolve_backward

def checked(doc,profile,path,existing=None):
    if existing and not getattr(existing,'FluxPartialSweep',False):raise ValueError('Create a new partial sweep;native sweep representation cannot change.')
    if profile==path:raise ValueError('Select different profile and path')
    for source in (profile,path):
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic sweep reference')
        if any('Invalid' in x.State or 'Error' in x.State or bool(getattr(x,'Error','')) for x in [source]+list(source.OutListRecursive)):raise ValueError('Repair source errors first')
        if source.Shape.isNull() or not source.Shape.isValid():raise ValueError('Sweep source is empty or invalid')

def bounded(wire):
    if not 1<=len(wire.Edges)<=200 or not math.isfinite(wire.Length) or not 1e-7<wire.Length<=1e7:raise ValueError('Use1..200 edges and finite length >1e-7..1e7mm')
    box=wire.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)):raise ValueError('Input bounds exceed +/-1000000mm')
    for edge in wire.Edges:
        curve=edge.Curve
        if isinstance(curve,(Part.Line,Part.Circle,Part.Ellipse)):continue
        if isinstance(curve,(Part.BSplineCurve,Part.BezierCurve)) and 1<=curve.Degree<=9 and 2<=curve.NbPoles<=200:continue
        raise ValueError('Unsupported or overly complex sweep curve')

def shape(profile,path,frenet=False,transition=1,path_fraction=None,backward_fraction=None):
    import model_sections
    checked(profile.Document if profile else None,profile,path)
    fraction=resolve_fraction(path_fraction)
    if type(frenet) is not bool or type(transition) is not int or transition not in (0,1,2):raise ValueError('Invalid sweep frame or transition')
    section=model_sections.wire(profile);spine=model_sections.wire(path,False);bounded(section);bounded(spine)
    if not isinstance(Part.Face(section).Surface,Part.Plane):raise ValueError('Use a planar closed profile')
    backward=resolve_backward(backward_fraction)
    out=span(spine,fraction,backward).makePipeShell([section],True,frenet,transition)
    if out.isNull() or not out.isValid() or len(out.Solids)!=1 or out.Volume<=1e-9:raise ValueError('Sweep did not produce one valid solid')
    box=out.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)):raise ValueError('Sweep bounds exceed +/-1000000mm')
    # Identity outer location preserves native world geometry when assigning Shape.
    return Part.makeCompound([out])

class PartialSweep:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            inputs=list(obj.FluxSections)+[obj.FluxPath]
            checked(obj.Document,inputs[0],inputs[1],obj)
            if hierarchy(inputs)!=list(obj.SourceHierarchy):raise ValueError('Source hierarchy changed;reselect inputs')
            out=shape(inputs[0],inputs[1],obj.Frenet,obj.getEnumerationsOfProperty('Transition').index(obj.Transition),obj.PathFraction,float(getattr(obj,'BackwardFraction',0)))
            obj.Shape=out;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,profile,path,frenet=False,transition=1,path_fraction=None,existing=None,backward_fraction=None):
    from model_features import placed_preview,verify_result
    checked(doc,profile,path,existing);fraction=resolve_fraction(path_fraction,float(existing.PathFraction) if existing else None)
    backward=resolve_backward(backward_fraction,float(getattr(existing,'BackwardFraction',0)) if existing else 0)
    expected=placed_preview(shape(profile,path,frenet,transition,fraction,backward),existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Partial Sweep'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','PartialSweep')
            for typ,key in [('App::PropertyBool','FluxSweep'),('App::PropertyBool','FluxPartialSweep'),('App::PropertyBool','Solid'),('App::PropertyBool','Frenet'),('App::PropertyEnumeration','Transition'),('App::PropertyFloat','PathFraction'),('App::PropertyLinkListGlobal','Sections'),('App::PropertyLinkListGlobal','FluxSections'),('App::PropertyLinkGlobal','FluxPath'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxSweep=True;obj.FluxPartialSweep=True;obj.Solid=True;obj.Transition=['Transformed','Right corner','Round corner'];PartialSweep(obj);obj.ViewObject.Proxy=0
            for key in ('FluxSweep','FluxPartialSweep','Sections','FluxSections','FluxPath','SourceContainers','SourceHierarchy'):obj.setEditorMode(key,2)
            for key in ('Solid','Error'):obj.setEditorMode(key,1)
        if 'BackwardFraction' not in obj.PropertiesList:obj.addProperty('App::PropertyFloat','BackwardFraction','FluxCAD')
        obj.BackwardFraction=backward
        obj.Sections=[profile];obj.FluxSections=[profile];obj.FluxPath=path;obj.SourceContainers=parents([profile,path]);obj.SourceHierarchy=hierarchy([profile,path]);obj.Frenet=frenet;obj.Transition=transition;obj.PathFraction=fraction;obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,expected)
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later feature invalid;edit cancelled')
        profile.Visibility=False;path.Visibility=False;obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxPartialSweep',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SourceContainers)) for s in list(obj.FluxSections)+[obj.FluxPath]):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_partial_sweep_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_partial_sweep_observer=observer
install_observer()
