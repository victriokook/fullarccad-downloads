"""Isolated native Draft pipeline; not adopted until native and Qt review."""
import FreeCAD as App
import Part
import model
from model_defeature import containers
from unstitch_stamp import shape_fingerprint
from angle_chamfer_reference import reference_matches
from solid_draft_input import checked_input

class DraftInput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        try:
            source=obj.Source
            if not source or source.Document!=obj.Document or any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):
                raise ValueError('Repair source errors first.')
            if containers(source)!=list(obj.SourceContainers) or not reference_matches(source.Shape,obj.ReferenceShape):
                raise ValueError('Source geometry or hierarchy changed; reselect faces.')
            shape,_,_,_=checked_input(source,obj.FaceNames,obj.NeutralName,obj.DraftAngle)
            obj.Shape=shape;obj.Error=''
        except Exception as error:obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

class DraftOutput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            base=obj.Input;native=obj.Native
            if not base or not native or base.Error or 'Invalid' in native.State or base.Shape.isNull():
                raise ValueError(getattr(base,'Error','') or 'Native Draft failed.')
            _,names,_,angle=checked_input(base.Source,base.FaceNames,base.NeutralName,base.DraftAngle)
            if abs(float(native.Angle)-angle)>1e-10 or native.Base[0]!=base or list(native.Base[1])!=names or native.NeutralPlane[0]!=base or list(native.NeutralPlane[1])!=[base.NeutralName]:
                raise ValueError('Native Draft settings do not match checked inputs.')
            result=native.Shape.copy()
            if result.isNull() or not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:
                raise ValueError('Draft did not produce one valid solid.')
            boundary=Part.makeCompound(result.Faces)
            for name in names:
                face=base.Shape.getElement(name)
                if face.common(boundary).Area>max(1e-7,face.Area*1e-7):raise ValueError('A selected face remains undrafted.')
            result.Placement=base.Source.getGlobalPlacement().multiply(result.Placement)
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def internal(obj):
    obj.addProperty('App::PropertyBool','FluxCADInternal','FluxCAD');obj.FluxCADInternal=True;obj.setEditorMode('FluxCADInternal',2);obj.Visibility=False
    return obj

def create(doc,source,names,neutral,angle,reverse=False):
    if source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select a source in the active document.')
    doc.recompute()
    shape,names,neutral,angle=checked_input(source,names,neutral,angle)
    body=internal(doc.addObject('PartDesign::Body','DraftInternalBody'))
    base=internal(body.newObject('PartDesign::FeaturePython','DraftCheckedInput'))
    for typ,name in [('App::PropertyLinkGlobal','Source'),('App::PropertyLinkListGlobal','SourceContainers'),('Part::PropertyPartShape','ReferenceShape'),('App::PropertyStringList','FaceNames'),('App::PropertyString','NeutralName'),('App::PropertyFloat','DraftAngle'),('App::PropertyString','Error')]:base.addProperty(typ,name,'FluxCAD')
    base.Source=source;base.SourceContainers=containers(source);base.ReferenceShape=source.Shape.copy();base.FaceNames=names;base.NeutralName=neutral;base.DraftAngle=angle
    DraftInput(base);base.ViewObject.Proxy=0;doc.recompute()
    native=internal(body.newObject('PartDesign::Draft','DraftNative'))
    native.Base=(base,names);native.NeutralPlane=(base,[neutral]);native.Angle=angle;native.Reversed=bool(reverse)
    out=doc.addObject('Part::FeaturePython','SolidDraft')
    for typ,name in [('App::PropertyBool','FluxSolidDraft'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','Input'),('App::PropertyLinkGlobal','Native'),('App::PropertyLink','InternalBody'),('App::PropertyString','Error')]:out.addProperty(typ,name,'FluxCAD')
    out.FluxSolidDraft=True;out.Source=source;out.Input=base;out.Native=native;out.InternalBody=body
    DraftOutput(out);out.ViewObject.Proxy=0;doc.recompute()
    for helper in (body,base,native):helper.Visibility=False
    if out.Error or out.Shape.isNull() or 'Invalid' in native.State:raise ValueError(out.Error or base.Error or 'Native Draft failed to recompute.')
    out.Visibility=True
    return out




class FailureObserver:
    """Clear a stale visible result when FreeCAD skips downstream execution."""
    def slotRecomputedDocument(self,doc):
        for obj in list(doc.Objects):
            if not getattr(obj,'FluxSolidDraft',False):continue
            base=getattr(obj,'Input',None);native=getattr(obj,'Native',None)
            if not base or not native or base.Error or 'Invalid' in native.State or base.Shape.isNull():
                message=getattr(base,'Error','') or 'Native Draft failed.'
                if not obj.Shape.isNull():obj.Shape=Part.Shape()
                if obj.Error!=message:obj.Error=message

def install_observer():
    old=getattr(App,'_flux_solid_draft_failure_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=FailureObserver();App.addDocumentObserver(observer);App._flux_solid_draft_failure_observer=observer

install_observer()



def checked_existing(doc,source,existing=None):
    if not source or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select a source in the current document.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxSolidDraft',False) or existing.Source!=source or source==existing or existing in source.OutListRecursive):
        raise ValueError('Edit a Draft with the same source; cyclic references are not allowed.')

def preview(doc,source,names,neutral,angle,reverse=False,existing=None):
    checked_existing(doc,source,existing)
    doc.openTransaction('Preview Solid Draft')
    try:
        obj=create(doc,source,names,neutral,angle,reverse)
        result=model.world_shape(obj)
        if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
        return result
    finally:
        doc.abortTransaction();doc.recompute()

def apply(doc,source,names,neutral,angle,reverse=False,existing=None):
    checked_existing(doc,source,existing)
    expected=preview(doc,source,names,neutral,angle,reverse,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,'Solid Face Draft'):
        if existing:
            _,names,neutral,angle=checked_input(source,names,neutral,angle)
            obj=existing;base=obj.Input;native=obj.Native
            base.ReferenceShape=source.Shape.copy();base.SourceContainers=containers(source);base.FaceNames=names;base.NeutralName=neutral;base.DraftAngle=angle
            native.Base=(base,names);native.NeutralPlane=(base,[neutral]);native.Angle=angle;native.Reversed=bool(reverse)
            base.touch();native.touch();obj.touch();doc.recompute()
        else:obj=create(doc,source,names,neutral,angle,reverse)
        actual=model.world_shape(obj)
        if obj.Error or actual.isNull() or not actual.isValid() or actual.cut(expected).Volume+expected.cut(actual).Volume>max(1e-6,expected.Volume*1e-7):
            raise ValueError(obj.Error or 'Preview and result do not match.')
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and not child.Shape.Solids))):
                raise ValueError('The edit was cancelled because a later feature would become invalid.')
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
            if getattr(obj,'FluxSolidDraft',False):
                base=obj.Input;source=base.Source
                if source and (source.Name in members or changed in containers(source) or changed in list(base.SourceContainers)):
                    base.touch();obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}

def install_hierarchy_observer():
    old=getattr(App,'_flux_solid_draft_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_solid_draft_hierarchy_observer=observer

install_hierarchy_observer()
