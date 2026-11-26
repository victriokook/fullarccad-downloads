"""Guarded native surface loft of whole open wire profiles."""
import math
import FreeCAD as App
import Part,model
from model_defeature import containers
from surface_loft_options import validate_options

def bounded(shape):
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (shape.BoundBox.XMin,shape.BoundBox.YMin,shape.BoundBox.ZMin,shape.BoundBox.XMax,shape.BoundBox.YMax,shape.BoundBox.ZMax)):raise ValueError('Surface loft coordinates exceed +/-1000000mm')

def profile(source):
    shape=model.world_shape(source)
    if shape.isNull() or not shape.isValid() or shape.Faces or shape.Solids:raise ValueError('Use one whole open wire profile without faces or solids')
    if shape.ShapeType=='Edge':wire=Part.Wire([shape])
    elif len(shape.Wires)==1 and len(shape.Wires[0].Edges)==len(shape.Edges) and len(shape.Vertexes)==len(shape.Wires[0].Vertexes):wire=shape.Wires[0]
    else:raise ValueError('Use one connected open wire without extra elements')
    edges=wire.OrderedEdges
    if wire.isClosed() or not 1<=len(edges)<=20 or not 1e-7<wire.Length<=1e7:raise ValueError('Open profile requires1..20 edges,length>1e-7..1e7mm')
    bounded(wire)
    for edge in edges:
        curve=edge.Curve
        if isinstance(curve,(Part.Line,Part.Circle,Part.Ellipse)):pass
        elif isinstance(curve,(Part.BSplineCurve,Part.BezierCurve)):
            if not 1<=curve.Degree<=9 or not 2<=curve.NbPoles<=50:raise ValueError('Profile curve complexity exceeds degree9/poles50')
            if any(not math.isfinite(v) or abs(v)>1e6 for pole in curve.getPoles() for v in tuple(pole)):raise ValueError('Profile control poles exceed coordinate limits')
        else:raise ValueError('Unsupported profile curve')
        if not math.isfinite(edge.Length) or edge.Length<=1e-7:raise ValueError('Degenerate profile edge')
    return wire

def checked(doc,sections,existing=None):
    if type(sections) not in (list,tuple):raise ValueError('Select an ordered list of profiles')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxSurfaceLoft',False)):raise ValueError('Create a new surface loft;existing solid loft cannot change representation')
    if len(set(sections))!=len(sections):raise ValueError('Repeated surface-loft profiles are excluded')
    for source in sections:
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link') or not hasattr(source,'Shape'):raise ValueError('Select live current-document non-Link wire profiles')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic surface-loft reference')
        if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [source]+list(source.OutListRecursive)):raise ValueError('Repair profile source errors')

def shape(sections,ruled=False,closed=False):
    if type(sections) not in (list,tuple):raise ValueError('Select an ordered profile list')
    validate_options(len(sections),ruled,closed)
    if not sections:raise ValueError('Missing profiles')
    if sections[0] is None or not hasattr(sections[0],'Document'):raise ValueError('Missing first profile')
    checked(sections[0].Document,sections)
    wires=[profile(s) for s in sections];counts=[len(w.Edges) for w in wires]
    if len(set(counts))!=1 or sum(counts)>200:raise ValueError('Profiles require equal edge counts and at most200 total edges')
    try:result=Part.makeLoft(wires,False,ruled,False,5)
    except (Part.OCCError,RuntimeError) as error:raise ValueError('Cannot create a surface loft from these profiles') from error
    if result.isNull() or not result.isValid() or result.Solids or not 1<=len(result.Faces)<=200 or len(result.Shells)!=1 or not math.isfinite(result.Area) or result.Area<=1e-9:raise ValueError('Surface loft must yield one valid connected shell,1..200 faces')
    bounded(result)
    try:result.check(True)
    except (ValueError,Part.OCCError,RuntimeError) as error:raise ValueError('Surface loft contains a self-intersection or invalid topology') from error
    for wire in (wires[0],wires[-1]):
        for edge in wire.Edges:
            common=result.common(edge)
            if abs(sum(e.Length for e in common.Edges)-edge.Length)>max(1e-7,edge.Length*1e-7):raise ValueError('Loft does not retain its end profile')
    return Part.makeCompound([result])

def parents(sections):
    result=[]
    for source in sections:
        for parent in containers(source):
            if parent not in result:result.append(parent)
    return result

def hierarchy(sections):return [s.Name+':'+','.join(p.Name for p in containers(s)) for s in sections]

def preview(sections,ruled=False,closed=False,existing=None):
    result=shape(sections,ruled,closed)
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result

class SurfaceLoft:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            sections=list(obj.FluxSections);checked(obj.Document,sections,obj)
            if hierarchy(sections)!=list(obj.SectionHierarchy):raise ValueError('Profile hierarchy changed;reselect profiles')
            if obj.Solid or obj.MaxDegree!=5 or list(obj.Sections)!=sections:raise ValueError('Surface loft settings changed;reselect profiles')
            result=shape(sections,obj.Ruled,obj.Closed);obj.Shape=result;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,sections,ruled=False,closed=False,existing=None):
    validate_options(len(sections),ruled,closed);checked(doc,sections,existing);expected=preview(sections,ruled,closed,existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Surface Loft'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','SurfaceLoft')
            for typ,key in [('App::PropertyBool','FluxLoft'),('App::PropertyBool','FluxSurfaceLoft'),('App::PropertyBool','Ruled'),('App::PropertyBool','Closed'),('App::PropertyBool','Solid'),('App::PropertyInteger','MaxDegree'),('App::PropertyLinkListGlobal','Sections'),('App::PropertyLinkListGlobal','FluxSections'),('App::PropertyLinkListGlobal','SectionContainers'),('App::PropertyStringList','SectionHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxLoft=True;obj.FluxSurfaceLoft=True;SurfaceLoft(obj);obj.ViewObject.Proxy=0
            from i18n import tr
            obj.Label=tr('サーフェスロフト','Surface Loft')
            for key in ('FluxLoft','FluxSurfaceLoft','Sections','FluxSections','SectionContainers','SectionHierarchy'):obj.setEditorMode(key,2)
            for key in ('Ruled','Closed','Solid','MaxDegree','Error'):obj.setEditorMode(key,1)
        obj.Sections=list(sections);obj.FluxSections=list(sections);obj.SectionContainers=parents(sections);obj.SectionHierarchy=hierarchy(sections);obj.Ruled=ruled;obj.Closed=False;obj.Solid=False;obj.MaxDegree=5;obj.touch();doc.recompute()
        actual=model.world_shape(obj)
        if obj.Error or actual.isNull() or not actual.isValid() or actual.Solids:raise ValueError(obj.Error or 'Invalid surface result')
        tolerance=max(1e-7,expected.Area*1e-7)
        if abs(actual.Area-expected.Area)>tolerance or abs(actual.common(expected).Area-expected.Area)>tolerance:raise ValueError('Surface loft differs from preview')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or 'Error' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later feature lost geometry;surface loft edit cancelled')
        for source in sections:source.Visibility=False
        if not existing:obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        members=self.previous.pop((changed.Document.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in changed.Document.Objects:
            if getattr(obj,'FluxSurfaceLoft',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SectionContainers)) for s in obj.FluxSections):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_surface_loft_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_surface_loft_observer=observer
install_observer()
