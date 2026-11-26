"""Open straight sketch contour to a guarded native SheetMetal base wall."""
import math
from types import SimpleNamespace
import FreeCAD as App,Part
import model,sheetmetal_bridge
from model_hem import bounded
from model_point_loft import parents,hierarchy
from model_defeature import containers
from contour_values import values

def checked(source,existing=None):
    doc=App.ActiveDocument
    if source is None or source.Document!=doc or doc.getObject(source.Name)!=source or source.TypeId!='Sketcher::SketchObject':raise ValueError('Select a whole current-document planar sketch')
    if existing and (not getattr(existing,'FluxContour',False) or source==existing or existing in source.OutListRecursive):raise ValueError('Invalid or cyclic contour reference')
    if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [source]+list(source.OutListRecursive)):raise ValueError('Repair source errors first')
    base=model.world_shape(source)
    if base.isNull() or not base.isValid() or len(base.Wires)!=1 or base.Faces or base.Wires[0].isClosed() or not 1<=len(base.Edges)<=50:raise ValueError('Use one open sketch wire with1..50 straight segments')
    bounded(base);wire=base.Wires[0];edges=wire.OrderedEdges
    if len(wire.Vertexes)!=len(edges)+1 or len(base.Edges)!=len(edges) or len(base.Vertexes)!=len(wire.Vertexes):raise ValueError('Repeated,branched or extra geometry is not supported')
    for edge in edges:
        if not isinstance(edge.Curve,Part.Line) or edge.Length<=1e-6:raise ValueError('Use straight segments longer than1e-6mm')
    for i,first in enumerate(edges):
        for second in edges[i+2:]:
            if first.distToShape(second)[0]<1e-7:raise ValueError('Self-intersecting contours are not supported')
    pose=source.getGlobalPlacement();normal=pose.Rotation.multVec(App.Vector(0,0,1))
    if any(abs((v.Point-pose.Base).dot(normal))>1e-6 for v in wire.Vertexes):raise ValueError('Sketch must be planar in its XY plane')
    for first,second in zip(edges,edges[1:]):
        # The common corner angle is independent of edge parameter orientation.
        shared=next((a.Point for a in first.Vertexes for b in second.Vertexes if (a.Point-b.Point).Length<1e-7),None)
        if shared is None:raise ValueError('Sketch segments must be connected')
        a=next(v.Point-shared for v in first.Vertexes if (v.Point-shared).Length>1e-7);b=next(v.Point-shared for v in second.Vertexes if (v.Point-shared).Length>1e-7)
        angle=math.degrees(a.getAngle(b))
        if not 10<=angle<=170:raise ValueError('Internal corner angles must be10..170degrees')
    return base

def shape(source,thickness=1.,length=20.,radius=1.,side='Inside',midplane=False,reverse=False):
    sheetmetal_bridge.unavailable()

def settings(obj):return dict(thickness=obj.Thickness.Value,length=obj.Length.Value,radius=obj.Radius.Value,side=str(obj.Side),midplane=obj.Midplane,reverse=obj.Reverse)
def signature(source,existing=None):
    checked(source,existing)
    if existing and existing.ExpressionEngine:raise ValueError('Edit existing expressions in Properties')
    def stamp(o):return (o.Name,o.Shape.hashCode(),str(o.getGlobalPlacement()),tuple(o.State),str(getattr(o,'Error','')))
    return (tuple(stamp(o) for o in [source]+list(source.OutListRecursive) if hasattr(o,'Shape')),tuple(hierarchy([source])),None if existing is None else (stamp(existing),tuple(settings(existing).items())))
class Contour:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            checked(obj.Source,obj)
            if hierarchy([obj.Source])!=list(obj.SourceHierarchy):raise ValueError('Sketch hierarchy changed;reselect it')
            out=shape(obj.Source,**settings(obj));obj.Shape=out;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass
class ViewProvider:
    def __init__(self,vo):vo.Proxy=self
    def doubleClicked(self,vo):
        import FreeCADGui as Gui,contour_ui
        contour_ui.show(Gui.fluxcad_workspace,vo.Object);return True
    def dumps(self):return None
    def loads(self,state):pass
def apply(source,thickness=1.,length=20.,radius=1.,side='Inside',midplane=False,reverse=False,existing=None,expected=None):
    checked(source,existing)
    if existing and existing.ExpressionEngine:raise ValueError('Edit existing expressions in Properties')
    if expected is not None and signature(source,existing)!=expected:raise ValueError('Inputs changed;close and reopen')
    from model_features import placed_preview,verify_result
    preview=placed_preview(shape(source,thickness,length,radius,side,midplane,reverse),existing);doc=source.Document
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Contour Flange'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','ContourFlange')
            for typ,n in [('App::PropertyBool','FluxContour'),('App::PropertyLinkGlobal','Source'),('App::PropertyLength','Thickness'),('App::PropertyLength','Length'),('App::PropertyLength','Radius'),('App::PropertyEnumeration','Side'),('App::PropertyBool','Midplane'),('App::PropertyBool','Reverse'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,n,'ContourFlange')
            obj.FluxContour=True;obj.Side=['Inside','Outside','Middle'];Contour(obj);ViewProvider(obj.ViewObject)
            for n in ('FluxContour','Source','SourceContainers','SourceHierarchy'):obj.setEditorMode(n,2)
            obj.setEditorMode('Error',1)
        obj.Source=source;obj.SourceContainers=parents([source]);obj.SourceHierarchy=hierarchy([source]);obj.Thickness=thickness;obj.Length=length;obj.Radius=radius;obj.Side=side;obj.Midplane=midplane;obj.Reverse=reverse;obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,preview)
        for child in obj.InListRecursive:
            if getattr(child,'Error','') or 'Invalid' in child.State or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;contour edit cancelled')
        source.Visibility=False;obj.Visibility=True
    return obj
class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        members=self.previous.pop((changed.Document.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in changed.Document.Objects:
            if getattr(obj,'FluxContour',False) and obj.Source and (obj.Source.Name in members or changed in containers(obj.Source) or changed in list(obj.SourceContainers)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}
old=getattr(App,'_fullarc_contour_observer',None)
if old is not None:App.removeDocumentObserver(old)
App._fullarc_contour_observer=HierarchyObserver();App.addDocumentObserver(App._fullarc_contour_observer)
