"""Linked independent construction point at an explicit source VertexN."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from vertex_point_name import vertex_name
from model_construction import vertex

def checked(doc,source,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select a source in the current document.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxVertexPoint',False) or existing.Source!=source or source==existing or existing in source.OutListRecursive):raise ValueError('Select the same source; cyclic references are not allowed.')
    if not hasattr(source,'Shape') or any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')

def preview(doc,source,name,existing=None):
    checked(doc,source,existing);vertex_name(name,len(source.Shape.Vertexes));out=Part.Vertex(vertex((source,name)))
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

class VertexPoint:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Document,obj.Source,obj)
            if containers(obj.Source)!=list(obj.SourceContainers):raise ValueError('Source hierarchy changed; reselect the vertex.')
            out=preview(obj.Document,obj.Source,obj.VertexName)
            obj.Shape=Part.makeCompound([out]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,source,name,existing=None):
    expected=preview(doc,source,name,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,'Point at Vertex'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','VertexPoint')
            for typ,key in [('App::PropertyBool','FluxVertexPoint'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyString','VertexName'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxVertexPoint=True;obj.Source=source;VertexPoint(obj);obj.ViewObject.Proxy=0;obj.ViewObject.PointSize=8;obj.ViewObject.PointColor=(1.,.55,.1)
            for key in ('FluxVertexPoint','SourceContainers'):obj.setEditorMode(key,2)
            for key in ('Source','VertexName','Error'):obj.setEditorMode(key,1)
        obj.VertexName=name;obj.SourceContainers=containers(source);obj.touch();doc.recompute();out=model.world_shape(obj)
        if obj.Error or out.isNull() or len(out.Vertexes)!=1 or (out.Vertexes[0].Point-expected.Point).Length>1e-6:raise ValueError(obj.Error or 'Preview and result differ.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and not child.Shape.Solids))):raise ValueError('The edit was cancelled because a later feature would become invalid.')
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
            if getattr(obj,'FluxVertexPoint',False):
                source=getattr(obj,'Source',None)
                if source and (source.Name in members or changed in containers(source) or changed in list(obj.SourceContainers)):
                    obj.touch()
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_vertex_point_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_vertex_point_hierarchy_observer=observer

install_observer()
