"""Fail-closed point endpoint loft, evaluated by native Part.makeLoft."""
import FreeCAD as App
import Part
import model
from model_defeature import containers

def parents(sections):
    result=[]
    for source in sections:
        for parent in containers(source):
            if parent not in result:result.append(parent)
    return result

def hierarchy(sections):
    return [s.Name+':'+','.join(p.Name for p in containers(s)) for s in sections]

def checked(doc,sections,existing=None):
    if existing and not getattr(existing,'FluxPointLoft',False):
        raise ValueError('Create a new point loft; an existing native wire loft cannot change representation.')
    for source in sections:
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):
            raise ValueError('Select current-document non-Link sections.')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic section reference.')
        if any('Invalid' in o.State or 'Error' in o.State or bool(getattr(o,'Error','')) for o in [source]+list(source.OutListRecursive)):
            raise ValueError('Repair section source errors first.')
        if source.Shape.isNull() or not source.Shape.isValid():raise ValueError('Section is empty or invalid.')

class PointLoft:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            import model_sections
            sections=list(obj.FluxSections);checked(obj.Document,sections,obj)
            if hierarchy(sections)!=list(obj.SectionHierarchy):raise ValueError('Section hierarchy changed; reselect sections.')
            shape=model_sections.loft_shape(sections,obj.Ruled,obj.Closed)
            obj.Shape=shape;obj.Placement=pose;obj.Error=''
        except Exception as error:
            obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def create(doc,sections,ruled=False,closed=False,existing=None):
    import model_sections
    from model_features import placed_preview,verify_result
    checked(doc,sections,existing)
    expected=placed_preview(model_sections.loft_shape(sections,ruled,closed),existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Point Endpoint Loft'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','PointLoft')
            for typ,key in [('App::PropertyBool','FluxLoft'),('App::PropertyBool','FluxPointLoft'),('App::PropertyBool','Ruled'),('App::PropertyBool','Closed'),('App::PropertyBool','Solid'),('App::PropertyInteger','MaxDegree'),('App::PropertyLinkListGlobal','Sections'),('App::PropertyLinkListGlobal','FluxSections'),('App::PropertyLinkListGlobal','SectionContainers'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.addProperty('App::PropertyStringList','SectionHierarchy','FluxCAD');obj.setEditorMode('SectionHierarchy',2)
            obj.FluxLoft=True;obj.FluxPointLoft=True;obj.Solid=True;obj.MaxDegree=5;PointLoft(obj);obj.ViewObject.Proxy=0
            for key in ('FluxLoft','FluxPointLoft','Sections','FluxSections','SectionContainers'):obj.setEditorMode(key,2)
            for key in ('Ruled','Closed','Solid','MaxDegree','Error'):obj.setEditorMode(key,1)
        obj.Sections=list(sections);obj.FluxSections=list(sections);obj.SectionContainers=parents(sections);obj.SectionHierarchy=hierarchy(sections);obj.Ruled=ruled;obj.Closed=closed;obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,expected)
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later feature invalid; edit cancelled.')
        for source in sections:source.Visibility=False
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
            if getattr(obj,'FluxPointLoft',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SectionContainers)) for s in obj.FluxSections):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_point_loft_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_point_loft_observer=observer
install_observer()
