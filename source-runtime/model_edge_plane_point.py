"""Linked construction point at the extended intersection of a straight edge and a plane."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from model_construction import element,edge,face
from edge_plane_incidence import check_incidence
from edge_intersection_bounds import checked_coordinates

def checked(doc,a,b,existing=None):
    for ref in (a,b):
        if type(ref) not in (tuple,list) or len(ref)!=2:raise ValueError('Select two explicit edges.')
        source=ref[0]
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select sources in the current document.')
        if source.isDerivedFrom('App::Link'):raise ValueError('Links are excluded.')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic point reference.')
        if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if a[0]==b[0] and a[1]==b[1]:raise ValueError('Select two different edges.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxEdgePlanePoint',False)):raise ValueError('Select an intersection point to edit.')

def preview(doc,a,b,existing=None):
    checked(doc,a,b,existing);curve=element(a,'Edge');origin,direction=edge(a);center,normal=face(b);check_incidence(direction.dot(normal))
    points,segments=curve.Curve.intersectCS(element(b,'Face').Surface)
    if len(points)!=1 or segments:raise ValueError('Select a unique edge-plane intersection.')
    point=App.Vector(*checked_coordinates((points[0].X,points[0].Y,points[0].Z)));out=Part.Vertex(point)
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

class EdgePlanePoint:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            if containers(obj.SourceA)!=list(obj.ContainersA) or containers(obj.SourceB)!=list(obj.ContainersB):raise ValueError('Source hierarchy changed; reselect edges.')
            out=preview(obj.Document,(obj.SourceA,obj.EdgeA),(obj.SourceB,obj.FaceB));obj.Shape=Part.makeCompound([out]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,a,b,existing=None):
    expected=preview(doc,a,b,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,'Point At Edge And Plane'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','EdgePlanePoint')
            for typ,key in [('App::PropertyBool','FluxEdgePlanePoint'),('App::PropertyLinkGlobal','SourceA'),('App::PropertyLinkGlobal','SourceB'),('App::PropertyLinkListGlobal','ContainersA'),('App::PropertyLinkListGlobal','ContainersB'),('App::PropertyString','EdgeA'),('App::PropertyString','FaceB'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxEdgePlanePoint=True;EdgePlanePoint(obj);obj.ViewObject.Proxy=0;obj.ViewObject.PointSize=8;obj.ViewObject.PointColor=(1.,.55,.1)
            for key in ('FluxEdgePlanePoint','ContainersA','ContainersB'):obj.setEditorMode(key,2)
            for key in ('SourceA','SourceB','EdgeA','FaceB','Error'):obj.setEditorMode(key,1)
        obj.SourceA=a[0];obj.EdgeA=a[1];obj.SourceB=b[0];obj.FaceB=b[1];obj.ContainersA=containers(a[0]);obj.ContainersB=containers(b[0]);obj.touch();doc.recompute();out=model.world_shape(obj)
        if obj.Error or out.isNull() or len(out.Vertexes)!=1 or (out.Vertexes[0].Point-expected.Point).Length>1e-6:raise ValueError(obj.Error or 'Preview and result differ.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and not child.Shape.Solids))):raise ValueError('Later feature invalid; edit cancelled.')
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
            if getattr(obj,'FluxEdgePlanePoint',False):
                for source,key in ((obj.SourceA,'ContainersA'),(obj.SourceB,'ContainersB')):
                    if source and (source.Name in members or changed in containers(source) or changed in list(getattr(obj,key))):obj.touch();break
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_edge_plane_point_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_edge_plane_point_observer=observer
install_observer()
