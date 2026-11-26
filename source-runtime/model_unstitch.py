"""Whole-body separation to individual linked face objects.
Geometry changes invalidate all faces; indices are never silently remapped.
"""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from unstitch_stamp import fingerprint,shape_fingerprint
from unstitch_limits import face_limit


def checked(doc,source):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:
        raise ValueError("Choose one source in this document")
    if any("Invalid" in o.State or getattr(o,"Error","") for o in [source]+source.OutListRecursive):
        raise ValueError("Repair source errors first")
    shape=source.Shape
    if shape.isNull() or not shape.isValid() or shape.ShapeType not in ("Solid","Shell"):
        raise ValueError("Choose one whole solid or shell")
    face_limit(len(shape.Faces))
    return source


def faces(doc,source):
    checked(doc,source);shape=model.world_shape(source)
    result=[face.copy() for face in shape.Faces]
    if any(not f.isValid() or f.Area<=1e-9 for f in result):raise ValueError("Invalid source face")
    return result


class Face:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            source=checked(obj.Document,obj.Source)
            if obj==source or obj in source.OutListRecursive:raise ValueError("Cyclic face reference")
            if fingerprint(source)!=shape_fingerprint(obj.ReferenceShape) or containers(source)!=list(obj.SourceContainers) or len(source.Shape.Faces)!=obj.FaceCount:
                raise ValueError("Source geometry or hierarchy changed; create a new separation")
            index=int(obj.FaceIndex)
            if not 0<=index<obj.FaceCount:raise ValueError("Invalid face index")
            obj.Shape=Part.makeCompound([model.world_shape(source).Faces[index].copy()]);obj.Placement=pose;obj.Error=""
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def apply(doc,source):
    result=faces(doc,source);stamp=fingerprint(source);visible=source.Visibility
    try:
        with model.transaction(doc,"Unstitch All Faces"):
            group=doc.addObject("App::DocumentObjectGroup","Unstitch");group.Label="Unstitch All Faces"
            for i,expected in enumerate(result):
                obj=doc.addObject("Part::FeaturePython","SeparatedFace")
                for typ,name in [("App::PropertyBool","FluxUnstitchFace"),("App::PropertyLinkGlobal","Source"),("App::PropertyLinkListGlobal","SourceContainers"),("App::PropertyString","SourceStamp"),("Part::PropertyPartShape","ReferenceShape"),("App::PropertyInteger","FaceIndex"),("App::PropertyInteger","FaceCount"),("App::PropertyString","Error")]:obj.addProperty(typ,name,"FluxCAD")
                obj.FluxUnstitchFace=True;obj.Source=source;obj.SourceContainers=containers(source);obj.SourceStamp=stamp;obj.ReferenceShape=source.Shape.copy();obj.FaceIndex=i;obj.FaceCount=len(result)
                for name in ('Source','FaceIndex','FaceCount','Error'):obj.setEditorMode(name,1)
                for name in ('SourceContainers','SourceStamp','ReferenceShape','FluxUnstitchFace'):obj.setEditorMode(name,2)
                obj.Label="Face %d"%(i+1);Face(obj);obj.ViewObject.Proxy=0;group.addObject(obj)
            doc.recompute()
            for obj,expected in zip(group.Group,result):
                if obj.Error or obj.Shape.isNull() or len(obj.Shape.Faces)!=1 or abs(obj.Shape.Area-expected.Area)>max(1e-7,expected.Area*1e-7) or obj.Shape.common(expected).Area<expected.Area-max(1e-7,expected.Area*1e-7):raise ValueError(obj.Error or "Extracted face differs from source")
            source.Visibility=False
        return group
    except Exception:
        if source.Document:source.Visibility=visible
        raise


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
            if getattr(obj,'FluxUnstitchFace',False):
                source=getattr(obj,'Source',None)
                if source and (source.Name in members or changed in containers(source) or changed in list(obj.SourceContainers)):
                    obj.touch()
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_unstitch_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_unstitch_hierarchy_observer=observer

install_observer()
