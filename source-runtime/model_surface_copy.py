"""Guarded public surface copy reusing the existing native SubShapeBinder input."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from surface_copy_faces import face_names

def checked(doc,source,names,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select faces in the current document; links excluded.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxSurfaceCopy',False) or source!=existing.Source):raise ValueError('Edit faces on the original source.')
    if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic surface reference.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if not hasattr(source,'Shape') or source.Shape.isNull() or not source.Shape.isValid():raise ValueError('The source shape is invalid or empty.')
    return face_names(names,len(source.Shape.Faces))

def preview(doc,source,names,existing=None):
    names=checked(doc,source,names,existing);shape=model.world_shape(source);out=Part.makeCompound([shape.getElement(name) for name in names])
    if not out.isValid() or out.Solids or len(out.Faces)!=len(names):raise ValueError('Cannot copy the selected faces.')
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

def equivalent(actual,expected):
    if actual.isNull() or not actual.isValid() or actual.Solids or len(actual.Faces)!=len(expected.Faces):return False
    tolerance=max(1e-7,expected.Area*1e-9)
    return abs(actual.Area-expected.Area)<=tolerance and abs(actual.common(expected).Area-expected.Area)<=tolerance

class SurfaceCopy:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            expected=preview(obj.Document,obj.Source,list(obj.FaceNames))
            if containers(obj.Source)!=list(obj.SourceContainers):raise ValueError('Source hierarchy changed; reselect faces.')
            native=obj.NativeInput
            if native is None or 'Invalid' in native.State:raise ValueError('The native face reference is invalid.')
            actual=model.world_shape(native)
            if not equivalent(actual,expected):raise ValueError('Native face reference differs from current selected faces; reselect.')
            obj.Shape=actual;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,source,names,existing=None):
    names=checked(doc,source,names,existing);expected=preview(doc,source,names,existing)
    downstream={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    old=existing.NativeInput if existing else None
    if old and any(o!=existing for o in old.InList):raise ValueError('The internal reference has external consumers.')
    with model.transaction(doc,'Copy Selected Faces'):
        native=model._internal(model._profile_binder(doc,source,list(names),'Surface copy reference'));doc.recompute();obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','SurfaceCopy')
            for typ,key in [('App::PropertyBool','FluxSurfaceCopy'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','NativeInput'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','FaceNames'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxSurfaceCopy=True;SurfaceCopy(obj);obj.ViewObject.Proxy=0;obj.ViewObject.ShapeColor=(.8,.69,.49)
            for key in ('FluxSurfaceCopy','NativeInput','SourceContainers'):obj.setEditorMode(key,2)
            for key in ('Source','FaceNames','Error'):obj.setEditorMode(key,1)
        obj.Source=source;obj.FaceNames=list(names);obj.SourceContainers=containers(source);obj.NativeInput=native;obj.touch();doc.recompute()
        if obj.Error or not equivalent(model.world_shape(obj),expected):raise ValueError(obj.Error or 'Preview and result differ.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not now for was,now in zip(downstream[child.Name],(bool(child.Shape.Solids),bool(child.Shape.Faces),bool(child.Shape.Edges))))))):raise ValueError('Later feature invalid; edit cancelled.')
        if old:doc.removeObject(old.Name)
        obj.Visibility=True;native.Visibility=False
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxSurfaceCopy',False) and obj.Source and (obj.Source.Name in members or changed in containers(obj.Source) or changed in list(obj.SourceContainers)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_surface_copy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_surface_copy_observer=observer
install_observer()
