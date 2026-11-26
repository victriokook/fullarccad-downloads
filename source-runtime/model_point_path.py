"""Linked point at arc distance on one whole edge."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from point_path_geometry import point


def checked(doc,source,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError("Choose a source edge in this document")
    if existing and (source==existing or existing in source.OutListRecursive):raise ValueError("Cyclic point reference")
    if any("Invalid" in o.State or getattr(o,"Error","") for o in [source]+source.OutListRecursive):raise ValueError("Repair source errors first")


def preview(doc,source,mode,value,reverse=False,existing=None):
    checked(doc,source,existing);result=point(model.world_shape(source),mode,value,reverse)
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result


class PointPath:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Document,obj.Source,obj)
            if containers(obj.Source)!=list(obj.SourceContainers):raise ValueError("Source hierarchy changed; reselect source")
            result=point(model.world_shape(obj.Source),str(obj.Mode),obj.Value,obj.Reverse);obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=""
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def apply(doc,source,mode,value,reverse=False,existing=None):
    if existing and (existing.Document!=doc or not getattr(existing,'FluxPointPath',False)):raise ValueError("Choose a path point feature to edit")
    expected=preview(doc,source,mode,value,reverse,existing)
    with model.transaction(doc,"Point Along Edge"):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','PointAlongEdge')
            for typ,name in [('App::PropertyBool','FluxPointPath'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyEnumeration','Mode'),('App::PropertyFloat','Value'),('App::PropertyBool','Reverse'),('App::PropertyString','Error')]:obj.addProperty(typ,name,'FluxCAD')
            obj.FluxPointPath=True;obj.Mode=['fraction','distance'];PointPath(obj);obj.ViewObject.Proxy=0;obj.ViewObject.PointSize=8;obj.ViewObject.PointColor=(1.,.55,.1)
            for name in ('FluxPointPath','SourceContainers'):obj.setEditorMode(name,2)
            for name in ('Source','Mode','Value','Reverse','Error'):obj.setEditorMode(name,1)
        obj.Source=source;obj.SourceContainers=containers(source);obj.Mode=mode;obj.Value=value;obj.Reverse=reverse;doc.recompute();actual=model.world_shape(obj)
        if obj.Error or actual.isNull() or len(actual.Vertexes)!=1 or (actual.Vertexes[0].Point-expected.Point).Length>1e-6:raise ValueError(obj.Error or "Preview/result point mismatch")
        for later in obj.InListRecursive:
            if 'Invalid' in later.State or getattr(later,'Error','') or (hasattr(later,'Shape') and (later.Shape.isNull() or not later.Shape.isValid())):raise ValueError("Later feature invalid; edit cancelled")
    return obj


class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:
            self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body'):return
        doc=changed.Document
        if not doc:return
        members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxPointPath',False):
                source=getattr(obj,'Source',None)
                if source and (source.Name in members or changed in containers(source) or changed in list(obj.SourceContainers)):
                    obj.touch()
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_point_path_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_point_path_hierarchy_observer=observer

install_observer()
