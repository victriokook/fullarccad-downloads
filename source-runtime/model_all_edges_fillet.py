"""Persistent whole-solid native fillet rule; isolated candidate."""
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part
import model
from model_defeature import containers
from all_edges_fillet_values import checked_radius,checked_edge_count


def checked_source(source):
    if not source or not hasattr(source,'Shape') or getattr(source,'FluxCADInternal',False):
        raise ValueError('Select a single solid body.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):
        raise ValueError('Repair source errors first.')
    shape=source.Shape.copy();shape.Placement=App.Placement()
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=1e-9:
        raise ValueError('Select one valid solid.')
    solid=shape.Solids[0]
    if len(shape.Faces)!=len(solid.Faces) or len(shape.Edges)!=len(solid.Edges) or len(shape.Vertexes)!=len(solid.Vertexes):
        raise ValueError('Extra faces, edges or points are not supported.')
    checked_edge_count(len(shape.Edges))
    return shape

class FilletInput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        try:
            checked_radius(obj.FilletRadius)
            obj.Shape=checked_source(obj.Source);obj.Error=''
        except Exception as error:obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

class FilletOutput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            base,native=obj.Input,obj.Native
            if not base or not native or base.Error or 'Invalid' in native.State:
                raise ValueError(getattr(base,'Error','') or 'Native all-edges fillet failed.')
            checked_source(base.Source)
            if not native.UseAllEdges or native.Base[0]!=base or list(native.Base[1]) or abs(native.Radius.Value-base.FilletRadius)>1e-10:
                raise ValueError('Native fillet settings changed. Reopen the command.')
            result=native.Shape.copy()
            if result.isNull() or not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:
                raise ValueError('Fillet did not produce one valid solid.')
            if result.cut(base.Shape).Volume+base.Shape.cut(result).Volume<=max(1e-8,base.Shape.Volume*1e-10):
                raise ValueError('No edge was filleted.')
            result.Placement=base.Source.getGlobalPlacement().multiply(result.Placement)
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def internal(obj):
    obj.addProperty('App::PropertyBool','FluxCADInternal','FluxCAD');obj.FluxCADInternal=True
    obj.setEditorMode('FluxCADInternal',2);obj.Visibility=False
    return obj


def build(doc,source,radius):
    checked_source(source);radius=checked_radius(radius)
    body=internal(doc.addObject('PartDesign::Body','AllEdgesFilletInternal'))
    base=internal(body.newObject('PartDesign::FeaturePython','AllEdgesFilletInput'))
    for typ,name in [('App::PropertyLinkGlobal','Source'),('App::PropertyFloat','FilletRadius'),('App::PropertyString','Error')]:base.addProperty(typ,name,'FluxCAD')
    base.Source=source;base.FilletRadius=radius;FilletInput(base);base.ViewObject.Proxy=0;doc.recompute()
    native=internal(body.newObject('PartDesign::Fillet','AllEdgesFilletNative'))
    native.Base=(base,[]);native.UseAllEdges=True;native.Radius=radius
    out=doc.addObject('Part::FeaturePython','AllEdgesFillet')
    for typ,name in [('App::PropertyBool','FluxAllEdgesFillet'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','Input'),('App::PropertyLinkGlobal','Native'),('App::PropertyLink','InternalBody'),('App::PropertyString','Error')]:out.addProperty(typ,name,'FluxCAD')
    out.FluxAllEdgesFillet=True;out.Source=source;out.Input=base;out.Native=native;out.InternalBody=body
    FilletOutput(out);out.ViewObject.Proxy=0;doc.recompute()
    for obj in (body,base,native):obj.Visibility=False
    if out.Error or out.Shape.isNull():raise ValueError(out.Error or 'Native fillet failed.')
    return out


def validate(doc,source,existing=None):
    if not source or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select a source in the active document.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxAllEdgesFillet',False) or existing.Source!=source or source==existing or existing in source.OutListRecursive):
        raise ValueError('Use the original source; cyclic references are not allowed.')


def preview(doc,source,radius,existing=None):
    validate(doc,source,existing);checked_source(source);checked_radius(radius)
    doc.openTransaction('Preview All Edges Fillet')
    try:
        out=build(doc,source,radius);shape=model.world_shape(out)
        if existing:shape.Placement=existing.getGlobalPlacement().multiply(shape.Placement)
        return shape
    finally:doc.abortTransaction();doc.recompute()


def apply(doc,source,radius,existing=None):
    expected=preview(doc,source,radius,existing)
    dimensions={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'All Edges Fillet'):
        if existing:
            out=existing;out.Input.FilletRadius=checked_radius(radius);out.Native.Radius=radius
            out.Native.Base=(out.Input,[]);out.Native.UseAllEdges=True
            out.Input.touch();out.Native.touch();out.touch();doc.recompute()
        else:out=build(doc,source,radius)
        actual=model.world_shape(out)
        if out.Error or actual.isNull() or actual.cut(expected).Volume+expected.cut(actual).Volume>max(1e-6,expected.Volume*1e-7):raise ValueError(out.Error or 'Preview and result differ.')
        for child in out.InListRecursive:
            shape=getattr(child,'Shape',None);old=dimensions.get(child.Name,(False,False,False))
            if 'Invalid' in child.State or getattr(child,'Error','') or (shape is not None and (shape.isNull() or not shape.isValid() or any(was and not now for was,now in zip(old,(bool(shape.Solids),bool(shape.Faces),bool(shape.Edges)))))):
                raise ValueError('The edit would invalidate a later feature.')
        source.Visibility=False;out.Visibility=True
    return out


def stamp(source,existing=None):
    def content(obj):
        if not obj:return None
        root=ET.fromstring('<Root>'+obj.Content+'</Root>')
        for props in root.iter('Properties'):
            for prop in list(props):
                if prop.attrib.get('name') in ('Shape','Visibility'):props.remove(prop)
        return ET.tostring(root,encoding='unicode')
    from unstitch_stamp import shape_fingerprint
    return (content(source),shape_fingerprint(source.Shape),str(source.getGlobalPlacement()),tuple(o.Name for o in containers(source)),content(existing),content(existing.Input) if existing else None,content(existing.Native) if existing else None)

class Observer:
    def __init__(self):self.previous={}
    def slotRecomputedDocument(self,doc):
        for out in list(doc.Objects):
            if not getattr(out,'FluxAllEdgesFillet',False):continue
            base,native=out.Input,out.Native
            if not base or not native or base.Error or 'Invalid' in native.State:
                if not out.Shape.isNull():out.Shape=Part.Shape()
                out.Error=getattr(base,'Error','') or 'Native all-edges fillet failed.'
    def slotBeforeChangeObject(self,obj,prop):
        if prop=='Group' and obj.TypeId in ('App::Part','PartDesign::Body') and obj.Document:self.previous[(obj.Document.Name,obj.Name)]={o.Name for o in obj.Group}
    def slotChangedObject(self,obj,prop):
        if prop!='Group' or obj.TypeId not in ('App::Part','PartDesign::Body') or not obj.Document:return
        members=self.previous.pop((obj.Document.Name,obj.Name),set())|{o.Name for o in obj.Group}
        for out in obj.Document.Objects:
            if getattr(out,'FluxAllEdgesFillet',False) and out.Source and (out.Source.Name in members or obj in containers(out.Source)):
                out.Input.touch();out.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_all_edges_fillet_observer',None)
    if old:App.removeDocumentObserver(old)
    App._flux_all_edges_fillet_observer=Observer();App.addDocumentObserver(App._flux_all_edges_fillet_observer)
install_observer()
