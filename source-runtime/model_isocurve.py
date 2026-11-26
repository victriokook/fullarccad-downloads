"""Linked finite analytic-face isoparametric curves."""
import FreeCAD as App
import Part
import model
from model_stitch import parents
from isocurve_geometry import build
from isocurve_values import validate
from isocurve_distribution import positions
from isocurve_link_mode import validate_linked


def checked(doc,source,existing=None):
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source:raise ValueError('Choose a face in this document')
    if existing and (source==existing or existing in source.OutListRecursive):raise ValueError('Cyclic isocurve reference')
    if any('Invalid' in o.State or getattr(o,'Error','') for o in [source]+source.OutListRecursive):raise ValueError('Repair source errors first')

def shape(source,axis,fraction,count=1):return build(model.world_shape(source),axis,fraction,count)

def preview(doc,source,axis,fraction,existing=None,count=None):
    if count is None:count=getattr(existing,"Count",1) if existing else 1
    checked(doc,source,existing);out=shape(source,axis,fraction,count)
    if existing:out.Placement=existing.getGlobalPlacement().multiply(out.Placement)
    return out

class IsoCurve:
    def __init__(self, obj): obj.Proxy = self
    def execute(self, obj):
        pose = App.Placement(obj.Placement)
        try:
            checked(obj.Document, obj.Source, obj)
            if parents([obj.Source]) != list(obj.SourceContainers):
                raise ValueError("Input hierarchy changed; reselect inputs")
            out = shape(obj.Source,obj.Axis,obj.Fraction,getattr(obj,"Count",1))
            obj.Shape = Part.makeCompound([out]); obj.Placement = pose; obj.Error = ""
        except Exception as error:
            obj.Shape = Part.Shape(); obj.Placement = pose; obj.Error = str(error)
    def dumps(self): return None
    def loads(self, state): pass


def apply(doc, source, axis, fraction, existing=None, count=None, linked=True):
    linked=validate_linked(linked,existing is not None)
    if existing and (existing.Document != doc or not getattr(existing,"FluxIsoCurve",False)):
        raise ValueError("Choose an isocurve feature to edit")
    axis,fraction=validate(axis,fraction)
    if count is None:count=getattr(existing,"Count",1) if existing else 1
    positions(count,fraction)
    expected = preview(doc,source,axis,fraction,existing,count)
    if not linked:return independent(doc,expected)
    downstream = {o.Name:(bool(o.Shape.Edges),bool(o.Shape.Faces),bool(o.Shape.Solids)) for o in existing.InListRecursive if hasattr(o,"Shape")} if existing else {}
    with model.transaction(doc,"Extract Isoparametric Curve"):
        obj = existing
        if obj is None:
            obj = doc.addObject("Part::FeaturePython","IsoCurve")
            for typ,name in [("App::PropertyBool","FluxIsoCurve"),("App::PropertyLinkGlobal","Source"),("App::PropertyLinkListGlobal","SourceContainers"),("App::PropertyString","Axis"),("App::PropertyFloat","Fraction"),("App::PropertyString","Error")]:obj.addProperty(typ,name,"FluxCAD")
            obj.FluxIsoCurve=True; obj.setEditorMode("FluxIsoCurve",2); obj.setEditorMode("SourceContainers",2)
            for name in ("Source","Axis","Fraction","Error"):obj.setEditorMode(name,1)
            IsoCurve(obj); obj.ViewObject.Proxy=0
        if "Count" not in obj.PropertiesList:obj.addProperty("App::PropertyInteger","Count","FluxCAD");obj.setEditorMode("Count",1)
        obj.Count=count
        obj.Source=source;obj.SourceContainers=parents([source]);obj.Axis=axis;obj.Fraction=fraction
        doc.recompute();actual=model.world_shape(obj)
        if obj.Error or actual.isNull() or not actual.isValid() or len(actual.Edges)!=len(expected.Edges) or abs(actual.Length-expected.Length)>max(1e-7,expected.Length*1e-7):
            raise ValueError(obj.Error or "Preview/result differ")
        for edge in actual.Edges:
            for point in edge.discretize(Number=17):
                if Part.Vertex(point).distToShape(expected)[0]>1e-6:raise ValueError("Preview/result positions differ")
        for later in obj.InListRecursive:
            if "Invalid" in later.State or getattr(later,"Error",""):raise ValueError("Later feature invalid; edit cancelled")
            if hasattr(later,"Shape"):
                was=downstream.get(later.Name,(False,False,False));now=(bool(later.Shape.Edges),bool(later.Shape.Faces),bool(later.Shape.Solids))
                if later.Shape.isNull() or not later.Shape.isValid() or any(a and not b for a,b in zip(was,now)):raise ValueError("Later geometry lost; edit cancelled")
        obj.Visibility=True
    return obj


def independent(doc,expected):
    """Create a standard static curve, with no link properties or Python execution proxy."""
    with model.transaction(doc,'Independent Isoparametric Curve'):
        obj=doc.addObject('Part::Feature','IndependentIsoCurve');obj.Label='Isoparametric Curve (Independent)'
        obj.addProperty('App::PropertyBool','FluxIndependentIsoCurve','FluxCAD');obj.FluxIndependentIsoCurve=True;obj.setEditorMode('FluxIndependentIsoCurve',2)
        obj.Shape=expected.copy();doc.recompute();actual=model.world_shape(obj)
        if actual.isNull() or not actual.isValid() or actual.Faces or actual.Solids or len(actual.Edges)!=len(expected.Edges) or abs(actual.Length-expected.Length)>max(1e-7,expected.Length*1e-9):raise ValueError('Independent curve shape mismatch')
        for edge,reference in zip(actual.Edges,expected.Edges):
            if abs(edge.common(reference).Length-edge.Length)>max(1e-7,edge.Length*1e-9):raise ValueError('Independent curve position mismatch')
        if obj.OutList:raise ValueError('Independent curve unexpectedly has dependencies')
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
            if getattr(obj,'FluxIsoCurve',False):
                source=getattr(obj,'Source',None)
                if source and (source.Name in members or changed in parents([source]) or changed in list(obj.SourceContainers)):
                    obj.touch()
    def slotDeletedDocument(self,doc):
        self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}


def install_observer():
    old=getattr(App,'_flux_isocurve_hierarchy_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_isocurve_hierarchy_observer=observer

install_observer()
