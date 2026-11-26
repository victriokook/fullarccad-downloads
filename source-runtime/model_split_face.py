"""Linked face imprint retaining every region and the original solid volume."""
import FreeCAD as App
import Part
import model
from model_stitch import parents
from angle_chamfer_reference import reference_matches
from split_face_geometry import build
from i18n import tr


def checked(doc, source, tool, existing=None):
    if not source or not tool or source==tool:
        raise ValueError('Select distinct source and tool objects')
    if existing and (existing.Document is not doc or not getattr(existing,'FluxSplitFace',False)):
        raise ValueError('Select a Split Face result')
    for obj in (source,tool):
        if (obj.Document is not doc or doc.getObject(obj.Name) is not obj
                or not hasattr(obj,'Shape') or (existing and (obj==existing or existing in obj.OutListRecursive))):
            raise ValueError('Select independent shapes in the active document')
        if any('Invalid' in o.State or getattr(o,'Error','') for o in [obj]+obj.OutListRecursive):
            raise ValueError('Repair source errors first')


def preview(doc, source, face, tool, existing=None):
    checked(doc,source,tool,existing)
    result=build(model.world_shape(source),face,model.world_shape(tool))
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result


class SplitFace:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Document,obj.Source,obj.Tool,obj)
            if (parents([obj.Source,obj.Tool])!=list(obj.SourceContainers)
                    or not reference_matches(obj.Source.Shape,obj.ReferenceShape)):
                raise ValueError('Source geometry or input hierarchy changed; reselect the face and tool')
            result=build(model.world_shape(obj.Source),obj.FaceName,model.world_shape(obj.Tool))
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def apply(doc, source, face, tool, existing=None):
    expected=preview(doc,source,face,tool,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,tr('面を分割', 'Split Face')):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','SplitFace');obj.Label=tr('面分割','Split Face')
            for typ,key in [('App::PropertyBool','FluxSplitFace'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','Tool'),('App::PropertyLinkListGlobal','SourceContainers'),('Part::PropertyPartShape','ReferenceShape'),('App::PropertyString','FaceName'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'FluxCAD')
            obj.FluxSplitFace=True;SplitFace(obj);obj.ViewObject.Proxy=0
            obj.ViewObject.ShapeColor=(.72,.79,.85)
            for key in ('FluxSplitFace','SourceContainers','ReferenceShape'):obj.setEditorMode(key,2)
            for key in ('Source','Tool','FaceName','Error'):obj.setEditorMode(key,1)
        obj.Source=source;obj.Tool=tool;obj.FaceName=face;obj.SourceContainers=parents([source,tool]);obj.ReferenceShape=source.Shape.copy();obj.touch()
        doc.recompute();actual=model.world_shape(obj)
        tol=max(1e-7,expected.Volume*1e-9)
        if (obj.Error or actual.isNull() or not actual.isValid() or len(actual.Solids)!=1
                or len(actual.Faces)!=len(expected.Faces)
                or actual.cut(expected).Volume+expected.cut(actual).Volume>tol):
            raise ValueError(obj.Error or 'Preview and result differ')
        for child in obj.InListRecursive:
            if ('Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and
                    (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and not child.Shape.Solids)))):
                raise ValueError('A dependent feature lost valid geometry; the edit was undone')
        source.Visibility=False;obj.Visibility=True
    return obj


class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:
            self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxSplitFace',False):
                sources=[o for o in (obj.Source,obj.Tool) if o]
                if (any(o.Name in members for o in sources) or changed in parents(sources)
                        or changed in list(obj.SourceContainers)):obj.touch()
    def slotRecomputedDocument(self,doc):
        for obj in doc.Objects:
            if getattr(obj,'FluxSplitFace',False):
                sources=[getattr(obj,key,None) for key in ('Source','Tool')]
                if any(not o or o.Shape.isNull() or 'Invalid' in o.State or getattr(o,'Error','') for o in sources):
                    if not obj.Shape.isNull():obj.Shape=Part.Shape()
                    obj.Error='Repair missing or invalid input geometry'
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_split_face_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_split_face_observer=observer


install_observer()
