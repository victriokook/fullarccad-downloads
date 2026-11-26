"""Restore finite native freeform surface boundaries with linked history."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from surface_copy_faces import face_names
from natural_untrim_geometry import restored

def checked(doc,source,names,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.isDerivedFrom('App::Link'):raise ValueError('Select faces in the current document; links excluded.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxNaturalUntrim',False) or source!=existing.Source):raise ValueError('Edit faces on the original source.')
    if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic surface reference.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    if not hasattr(source,'Shape') or source.Shape.isNull() or not source.Shape.isValid():raise ValueError('The source shape is invalid or empty.')
    names=face_names(names,len(source.Shape.Faces))
    if len(names)!=1:raise ValueError('Select exactly one face.')
    return names

def preview(doc,source,names,existing=None):
    names=checked(doc,source,names,existing);shape=model.world_shape(source);out=restored(shape.getElement(names[0]))
    if not out.isValid() or out.Solids or len(out.Faces)!=1:raise ValueError('Cannot copy the selected faces.')
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

def equivalent(actual,expected):
    if actual.isNull() or not actual.isValid() or actual.Solids or len(actual.Faces)!=len(expected.Faces):return False
    tolerance=max(1e-7,expected.Area*1e-9)
    return abs(actual.Area-expected.Area)<=tolerance and abs(actual.common(expected).Area-expected.Area)<=tolerance

class NaturalUntrim:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            expected=preview(obj.Document,obj.Source,list(obj.FaceNames))
            if containers(obj.Source)!=list(obj.SourceContainers):raise ValueError('Source hierarchy changed; reselect faces.')
            obj.Shape=Part.makeCompound([expected]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,source,names,existing=None):
    names=checked(doc,source,names,existing);expected=preview(doc,source,names,existing)
    downstream={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Restore Natural Surface Boundary'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','NaturalUntrim')
            for typ,key in [('App::PropertyBool','FluxNaturalUntrim'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','FaceNames'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxNaturalUntrim=True;NaturalUntrim(obj);obj.ViewObject.Proxy=0;obj.ViewObject.ShapeColor=(.8,.69,.49)
            for key in ('FluxNaturalUntrim','SourceContainers'):obj.setEditorMode(key,2)
            for key in ('Source','FaceNames','Error'):obj.setEditorMode(key,1)
        obj.Source=source;obj.FaceNames=list(names);obj.SourceContainers=containers(source);obj.touch();doc.recompute()
        if obj.Error or not equivalent(model.world_shape(obj),expected):raise ValueError(obj.Error or 'Preview and result differ.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not now for was,now in zip(downstream[child.Name],(bool(child.Shape.Solids),bool(child.Shape.Faces),bool(child.Shape.Edges))))))):raise ValueError('Later feature invalid; edit cancelled.')
        obj.Visibility=True;source.Visibility=False
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxNaturalUntrim',False) and obj.Source and (obj.Source.Name in members or changed in containers(obj.Source) or changed in list(obj.SourceContainers)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_natural_untrim_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_natural_untrim_observer=observer
install_observer()
