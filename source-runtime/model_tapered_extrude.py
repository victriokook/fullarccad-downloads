"""Native tapered extrusion of one planar profile; isolated candidate."""
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part
import math
from extrude_start_values import checked_offset,resolve_offset
import model
from model_defeature import containers
from tapered_extrude_values import checked_values
from two_side_taper_values import validate_second
from symmetric_taper_values import validate_extent
from holed_taper_limits import validate_counts

def extent(base):
    return validate_extent(getattr(base,"ExtentMode","sides"),base.Height,base.TaperAngle,getattr(base,"SecondHeight",0.),getattr(base,"SecondAngle",0.))

def mode_value(existing,mode):
    return getattr(existing.Input,"ExtentMode","sides") if mode is None and existing else ("sides" if mode is None else mode)


def checked_source(source):
    if not source or not hasattr(source,'Shape') or getattr(source,'FluxCADInternal',False):
        raise ValueError('Select one planar face or closed sketch wire.')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first.')
    shape=source.Shape.copy();shape.Placement=App.Placement()
    if shape.isNull() or not shape.isValid() or shape.Solids or shape.Shells:raise ValueError('Select a planar profile, not a solid or shell.')
    if len(shape.Faces)==1:
        face=shape.Faces[0]
        if len(shape.Edges)!=len(face.Edges) or len(shape.Vertexes)!=len(face.Vertexes):raise ValueError('Extra geometry is not supported.')
    elif not shape.Faces and shape.Wires:
        validate_counts(len(shape.Wires),len(shape.Edges))
        if any(not w.isClosed() for w in shape.Wires) or sum(len(w.Edges) for w in shape.Wires)!=len(shape.Edges) or sum(len(w.Vertexes) for w in shape.Wires)!=len(shape.Vertexes):raise ValueError('Use only closed wires, without extra geometry.')
        made=Part.makeFace(shape.Wires,'Part::FaceMakerBullseye')
        if len(made.Faces)!=1:raise ValueError('Use one outer region with nested holes, without islands or separate regions.')
        face=made.Faces[0]
    else:raise ValueError('Use exactly one planar face or a set of closed wires defining one region.')
    validate_counts(len(face.Wires),len(face.Edges))
    if not isinstance(face.Surface,Part.Plane) or not face.isValid() or face.Area<=1e-9:
        raise ValueError('Use one valid planar region with up to50 holes and200 straight/circular edges.')
    if any(not isinstance(edge.Curve,(Part.Line,Part.LineSegment,Part.Circle)) for edge in face.Edges):raise ValueError('Only straight and circular profile edges are supported.')
    return face

def start_face(source,value):
    value=checked_offset(value);face=checked_source(source)
    if value:
        face.translate(face.normalAt(0,0)*value)
        if any(not math.isfinite(x) or abs(x)>1e6 for v in face.Vertexes for x in tuple(v.Point)):
            raise ValueError('Offset profile coordinates exceed +/-1000000mm.')
    return face

def offset_value(existing,value):
    return resolve_offset(value,getattr(existing.Input,'StartOffset',0.) if existing else 0.)

def assign_start_dependencies(base,source):
    for typ,name in [('App::PropertyLinkListGlobal','StartContainers'),('App::PropertyStringList','StartHierarchy')]:
        if name not in base.PropertiesList:base.addProperty(typ,name,'FluxCAD')
    base.StartContainers=containers(source);base.StartHierarchy=[o.Name for o in containers(source)]

def check_start_face(base):
    expected=start_face(base.Source,getattr(base,'StartOffset',0.));actual=base.Shape
    if actual.isNull() or len(actual.Faces)!=1 or len(actual.Edges)!=len(expected.Edges) or len(actual.Wires)!=len(expected.Wires):
        raise ValueError('Start profile changed. Reopen the command.')
    if (actual.CenterOfMass-expected.CenterOfMass).Length>1e-7 or actual.normalAt(0,0).dot(expected.normalAt(0,0))<1-1e-10 or abs(actual.common(expected).Area-expected.Area)>max(1e-7,expected.Area*1e-9):
        raise ValueError('Start profile offset changed. Reopen the command.')

class TaperInput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        try:
            extent(obj)
            validate_second(getattr(obj,"SecondHeight",0.),getattr(obj,"SecondAngle",0.))
            if 'StartHierarchy' in obj.PropertiesList and list(obj.StartHierarchy)!=[o.Name for o in containers(obj.Source)]:
                raise ValueError('Source hierarchy changed. Reopen and reselect the source.')
            face=start_face(obj.Source,getattr(obj,'StartOffset',0.))
            # Assign the exact analytic shape, then explicitly synchronize the
            # internal object's placement (execute otherwise retains its old pose).
            desired=App.Placement(face.Placement)
            obj.Shape=face;obj.Placement=desired;obj.Error=''
        except Exception as error:obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

class TaperOutput:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            base,native=obj.Input,obj.Native
            if not base or not native or base.Error or 'Invalid' in native.State:
                raise ValueError(getattr(base,'Error','') or 'Native tapered extrusion failed.')
            check_start_face(base)
            forward,backward,back_angle,symmetric=extent(base)
            if native.Base!=base or native.DirMode!='Normal' or not native.Solid or native.Symmetric!=symmetric or abs(native.LengthRev.Value-backward)>1e-10 or abs(float(native.TaperAngleRev)-back_angle)>1e-10 or abs(native.LengthFwd.Value-forward)>1e-10 or abs(float(native.TaperAngle)-base.TaperAngle)>1e-10 or native.Reversed!=base.Reverse:
                raise ValueError('Native extrusion settings changed. Reopen the command.')
            result=native.Shape.copy()
            if result.isNull() or not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:
                raise ValueError('Tapered Extrude did not produce one valid solid.')
            total_height=forward+backward
            normal=base.Shape.normalAt(0,0)
            projections=[v.Point.dot(normal) for v in result.Vertexes]
            if not projections or abs(max(projections)-min(projections)-total_height)>max(1e-7,total_height*1e-8):raise ValueError('Extrusion did not reach the requested height.')
            if len(base.Shape.Wires)>1:
                caps=[f for f in result.Faces if isinstance(f.Surface,Part.Plane) and f.normalAt(0,0).cross(normal).Length<1e-7 and min(abs(f.CenterOfMass.dot(normal)-z) for z in (min(projections),max(projections)))<max(1e-7,total_height*1e-8)]
                if len(caps)!=2 or any(len(f.Wires)!=len(base.Shape.Wires) for f in caps):raise ValueError('A hole collapsed or changed topology at an end cap.')
            boundary=result if symmetric or backward>0 else Part.makeCompound(result.Faces)
            if abs(base.Shape.common(boundary).Area-base.Shape.Area)>max(1e-7,base.Shape.Area*1e-7):raise ValueError('The source profile cap is missing.')
            result.Placement=base.Source.getGlobalPlacement().multiply(result.Placement)
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def internal(obj):
    obj.addProperty('App::PropertyBool','FluxCADInternal','FluxCAD');obj.FluxCADInternal=True
    obj.setEditorMode('FluxCADInternal',2);obj.Visibility=False
    return obj


def build(doc,source,height,angle,reverse=False,second_height=0.,second_angle=0.,extent_mode="sides",start_offset=0.):
    start_offset=checked_offset(start_offset);checked_source(source);height,angle=checked_values(height,angle);second_height,second_angle=validate_second(second_height,second_angle)
    forward,backward,back_angle,symmetric=validate_extent(extent_mode,height,angle,second_height,second_angle)
    if type(reverse) is not bool:raise ValueError('Reverse must be boolean.')
    base=internal(doc.addObject('Part::FeaturePython','TaperedExtrudeInput'))
    for typ,name in [('App::PropertyLinkGlobal','Source'),('App::PropertyFloat','Height'),('App::PropertyFloat','TaperAngle'),('App::PropertyBool','Reverse'),('App::PropertyFloat','SecondHeight'),('App::PropertyFloat','SecondAngle'),('App::PropertyString','ExtentMode'),('App::PropertyFloat','StartOffset'),('App::PropertyString','Error')]:base.addProperty(typ,name,'FluxCAD')
    base.Source=source;base.Height=height;base.TaperAngle=angle;base.Reverse=reverse;base.SecondHeight=second_height;base.SecondAngle=second_angle;base.ExtentMode=extent_mode;base.StartOffset=start_offset;assign_start_dependencies(base,source);TaperInput(base);base.ViewObject.Proxy=0;doc.recompute()
    native=internal(doc.addObject('Part::Extrusion','TaperedExtrudeNative'))
    native.Base=base;native.DirMode='Normal';native.LengthFwd=forward;native.LengthRev=backward;native.TaperAngle=angle;native.TaperAngleRev=back_angle;native.Reversed=reverse;native.Symmetric=symmetric;native.Solid=True
    out=doc.addObject('Part::FeaturePython','TaperedExtrude')
    for typ,name in [('App::PropertyBool','FluxTaperedExtrude'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','Input'),('App::PropertyLinkGlobal','Native'),('App::PropertyString','Error')]:out.addProperty(typ,name,'FluxCAD')
    out.FluxTaperedExtrude=True;out.Source=source;out.Input=base;out.Native=native
    TaperOutput(out);out.ViewObject.Proxy=0;doc.recompute()
    for obj in (base,native):obj.Visibility=False
    if out.Error or out.Shape.isNull():raise ValueError(out.Error or 'Native tapered extrusion failed.')
    return out


def validate(doc,source,existing=None):
    if not source or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Select a source in the active document.')
    if existing and (existing.Document!=doc or not getattr(existing,'FluxTaperedExtrude',False) or existing.Source!=source or source==existing or existing in source.OutListRecursive):
        raise ValueError('Use the original source; cyclic references are not allowed.')


def second_values(existing,height,angle):
    base=existing.Input if existing else None
    return validate_second(getattr(base,'SecondHeight',0.) if height is None else height,getattr(base,'SecondAngle',0.) if angle is None else angle)


def preview(doc,source,height,angle,reverse=False,existing=None,second_height=None,second_angle=None,extent_mode=None,start_offset=None):
    second_height,second_angle=second_values(existing,second_height,second_angle)
    extent_mode=mode_value(existing,extent_mode)
    start_offset=offset_value(existing,start_offset)
    forward,backward,back_angle,symmetric=validate_extent(extent_mode,height,angle,second_height,second_angle)
    validate(doc,source,existing);checked_source(source);checked_values(height,angle)
    doc.openTransaction('Preview Tapered Extrude')
    try:
        out=build(doc,source,height,angle,reverse,second_height,second_angle,extent_mode,start_offset);shape=model.world_shape(out)
        if existing:shape.Placement=existing.getGlobalPlacement().multiply(shape.Placement)
        return shape
    finally:doc.abortTransaction();doc.recompute()


def apply(doc,source,height,angle,reverse=False,existing=None,second_height=None,second_angle=None,extent_mode=None,start_offset=None):
    second_height,second_angle=second_values(existing,second_height,second_angle)
    extent_mode=mode_value(existing,extent_mode)
    start_offset=offset_value(existing,start_offset)
    forward,backward,back_angle,symmetric=validate_extent(extent_mode,height,angle,second_height,second_angle)
    expected=preview(doc,source,height,angle,reverse,existing,second_height,second_angle,extent_mode,start_offset)
    dimensions={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Tapered Extrude'):
        if existing:
            out=existing;out.Input.Height,out.Input.TaperAngle=checked_values(height,angle);out.Input.Reverse=reverse
            for prop in ('SecondHeight','SecondAngle'):
                if prop not in out.Input.PropertiesList:out.Input.addProperty('App::PropertyFloat',prop,'FluxCAD')
            out.Input.SecondHeight=second_height;out.Input.SecondAngle=second_angle
            if "ExtentMode" not in out.Input.PropertiesList:out.Input.addProperty("App::PropertyString","ExtentMode","FluxCAD")
            out.Input.ExtentMode=extent_mode
            if "StartOffset" not in out.Input.PropertiesList:out.Input.addProperty("App::PropertyFloat","StartOffset","FluxCAD")
            out.Input.StartOffset=start_offset
            assign_start_dependencies(out.Input,source)
            out.Native.Symmetric=symmetric;out.Native.LengthRev=backward;out.Native.TaperAngleRev=back_angle
            out.Native.Base=out.Input;out.Native.LengthFwd=forward;out.Native.TaperAngle=angle;out.Native.Reversed=reverse
            out.Input.touch();out.Native.touch();out.touch();doc.recompute()
        else:out=build(doc,source,height,angle,reverse,second_height,second_angle,extent_mode,start_offset)
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
            if not getattr(out,'FluxTaperedExtrude',False):continue
            base,native=out.Input,out.Native
            if not base or not native or base.Error or 'Invalid' in native.State:
                if not out.Shape.isNull():out.Shape=Part.Shape()
                out.Error=getattr(base,'Error','') or 'Native tapered extrusion failed.'
    def slotBeforeChangeObject(self,obj,prop):
        if prop=='Group' and obj.TypeId in ('App::Part','PartDesign::Body') and obj.Document:self.previous[(obj.Document.Name,obj.Name)]={o.Name for o in obj.Group}
    def slotChangedObject(self,obj,prop):
        if prop!='Group' or obj.TypeId not in ('App::Part','PartDesign::Body') or not obj.Document:return
        members=self.previous.pop((obj.Document.Name,obj.Name),set())|{o.Name for o in obj.Group}
        for out in obj.Document.Objects:
            if getattr(out,'FluxTaperedExtrude',False) and out.Source and (out.Source.Name in members or obj in containers(out.Source)):
                out.Input.touch();out.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_tapered_extrude_observer',None)
    if old:App.removeDocumentObserver(old)
    App._flux_tapered_extrude_observer=Observer();App.addDocumentObserver(App._flux_tapered_extrude_observer)
install_observer()
