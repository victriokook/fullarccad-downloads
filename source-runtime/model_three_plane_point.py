"""Linked construction point at the extended intersection of three planar faces."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from model_construction import element,face
from three_plane_determinant import check_determinant
from edge_intersection_bounds import checked_coordinates

def checked(doc,a,b,c,existing=None):
    for ref in (a,b,c):
        if type(ref) not in (tuple,list) or len(ref)!=2:raise ValueError('Select three explicit faces.')
        source=ref[0]
        if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select sources in the current document.')
        if source.isDerivedFrom('App::Link'):raise ValueError('Links are excluded.')
        if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic point reference.')
        if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if len({(ref[0].Name,ref[1]) for ref in (a,b,c)})!=3:raise ValueError('Select three different faces.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxThreePlanePoint',False)):raise ValueError('Select an intersection point to edit.')

def preview(doc,a,b,c,existing=None):
    checked(doc,a,b,c,existing)
    normals=[face(ref)[1] for ref in (a,b,c)];check_determinant(normals[0].dot(normals[1].cross(normals[2])))
    planes=[element(ref,'Face').Surface for ref in (a,b,c)];lines=planes[0].intersectSS(planes[1])
    if len(lines)!=1 or not isinstance(lines[0],Part.Line):raise ValueError('Use a unique intersection line.')
    points,segments=lines[0].intersectCS(planes[2])
    if len(points)!=1 or segments:raise ValueError('Use a unique intersection point.')
    out=Part.Vertex(App.Vector(*checked_coordinates((points[0].X,points[0].Y,points[0].Z))))
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

class ThreePlanePoint:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            if any(containers(getattr(obj,'Source'+key))!=list(getattr(obj,'Containers'+key)) for key in 'ABC'):raise ValueError('Source hierarchy changed; reselect edges.')
            out=preview(obj.Document,(obj.SourceA,obj.FaceA),(obj.SourceB,obj.FaceB),(obj.SourceC,obj.FaceC));obj.Shape=Part.makeCompound([out]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,a,b,c,existing=None):
    expected=preview(doc,a,b,c,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,'Point Through Three Planes'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','ThreePlanePoint')
            for typ,key in [('App::PropertyBool','FluxThreePlanePoint'),('App::PropertyLinkGlobal','SourceA'),('App::PropertyLinkGlobal','SourceB'),('App::PropertyLinkGlobal','SourceC'),('App::PropertyLinkListGlobal','ContainersA'),('App::PropertyLinkListGlobal','ContainersB'),('App::PropertyLinkListGlobal','ContainersC'),('App::PropertyString','FaceA'),('App::PropertyString','FaceB'),('App::PropertyString','FaceC'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxThreePlanePoint=True;ThreePlanePoint(obj);obj.ViewObject.Proxy=0;obj.ViewObject.PointSize=8;obj.ViewObject.PointColor=(1.,.55,.1)
            for key in ('FluxThreePlanePoint','ContainersA','ContainersB','ContainersC'):obj.setEditorMode(key,2)
            for key in ('SourceA','SourceB','SourceC','FaceA','FaceB','FaceC','Error'):obj.setEditorMode(key,1)
        obj.SourceA=a[0];obj.FaceA=a[1];obj.SourceB=b[0];obj.FaceB=b[1];obj.SourceC=c[0];obj.FaceC=c[1];obj.ContainersA=containers(a[0]);obj.ContainersB=containers(b[0]);obj.ContainersC=containers(c[0]);obj.touch();doc.recompute();out=model.world_shape(obj)
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
            if getattr(obj,'FluxThreePlanePoint',False):
                for source,key in ((obj.SourceA,'ContainersA'),(obj.SourceB,'ContainersB'),(obj.SourceC,'ContainersC')):
                    if source and (source.Name in members or changed in containers(source) or changed in list(getattr(obj,key))):obj.touch();break
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_three_plane_point_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_three_plane_point_observer=observer
install_observer()
