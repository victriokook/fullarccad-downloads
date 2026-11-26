"""Linked analytic center point."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from center_point_geometry import point


def checked(doc,source,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError("Choose a surface in this document")
    if existing and (source==existing or existing in source.OutListRecursive):raise ValueError("Cyclic surface reference")
    if any("Invalid" in o.State or getattr(o,"Error","") for o in [source]+source.OutListRecursive):raise ValueError("Repair source errors first")


def preview(doc,source,existing=None):
    checked(doc,source,existing);out=point(model.world_shape(source))
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out


class CenterPoint:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Document,obj.Source,obj)
            if containers(obj.Source)!=list(obj.SourceContainers):raise ValueError("Source hierarchy changed; recreate operation")
            out=point(model.world_shape(obj.Source));obj.Shape=Part.makeCompound([out]);obj.Placement=pose;obj.Error=""
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def apply(doc,source):
    expected=preview(doc,source)
    with model.transaction(doc,"Analytic Center Point"):
        obj=doc.addObject("Part::FeaturePython","AnalyticCenterPoint")
        for typ,name in [("App::PropertyBool","FluxCenterPoint"),("App::PropertyLinkGlobal","Source"),("App::PropertyLinkListGlobal","SourceContainers"),("App::PropertyString","Error")]:obj.addProperty(typ,name,"FluxCAD")
        obj.FluxCenterPoint=True;obj.Source=source;obj.SourceContainers=containers(source)
        for name in ('FluxCenterPoint','SourceContainers'):obj.setEditorMode(name,2)
        for name in ('Source','Error'):obj.setEditorMode(name,1)
        CenterPoint(obj);obj.ViewObject.Proxy=0;obj.ViewObject.PointSize=8;obj.ViewObject.PointColor=(1.,.55,.1);doc.recompute();out=model.world_shape(obj)
        if obj.Error or out.isNull() or len(out.Vertexes)!=1 or (out.Vertexes[0].Point-expected.Point).Length>1e-6:raise ValueError(obj.Error or "Preview/result mismatch")
        obj.Visibility=True
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
            if getattr(obj,'FluxCenterPoint',False):
                source=getattr(obj,'Source',None)
                if source and (source.Name in members or changed in containers(source) or changed in list(obj.SourceContainers)):
                    obj.touch()
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_center_point_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_center_point_hierarchy_observer=observer

install_observer()
