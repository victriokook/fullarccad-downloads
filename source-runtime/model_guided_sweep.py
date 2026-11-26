"""Native auxiliary-spine orientation sweep,no contact and no profile scaling."""
import math
import FreeCAD as App,Part
import model
from model_point_loft import parents,hierarchy
from model_defeature import containers
from model_partial_sweep import bounded
from guided_frame_values import guide_normal

def checked(doc,profile,path,rail,existing=None):
    if existing and (existing.Document!=doc or doc.getObject(existing.Name)!=existing):raise ValueError('Edit a live guided sweep in the input document')
    if existing and not getattr(existing,'FluxGuidedSweep',False):raise ValueError('Create a new guided sweep;other sweep representations cannot change')
    if any(s is None for s in (profile,path,rail)) or len({profile,path,rail})!=3:raise ValueError('Select three different profile,path and guide objects')
    for s in (profile,path,rail):
        if s.Document!=doc or doc.getObject(s.Name)!=s or s.isDerivedFrom('App::Link'):raise ValueError('Select current-document non-Link inputs')
        if existing and (s==existing or existing in s.OutListRecursive):raise ValueError('Cyclic guided-sweep reference')
        if not hasattr(s,'Shape') or s.Shape.isNull() or not s.Shape.isValid():raise ValueError('Guided-sweep input is empty or invalid')
        if any('Invalid' in o.State or 'Error' in o.State or getattr(o,'Error','') for o in [s]+list(s.OutListRecursive)):raise ValueError('Repair input errors first')

def wire(source,profile=False):
    shape=model.world_shape(source)
    if shape.ShapeType=='Edge':shape=Part.Wire([shape])
    if shape.Solids or shape.Faces or len(shape.Wires)!=1 or len(shape.Wires[0].Edges)!=len(shape.Edges) or len(shape.Wires[0].Vertexes)!=len(shape.Vertexes):raise ValueError('Use a whole single wire or sketch without extra geometry')
    w=shape.Wires[0];bounded(w)
    if profile:
        if not w.isClosed():raise ValueError('The profile must be closed')
        try:face=Part.Face(w)
        except (Part.OCCError,RuntimeError):raise ValueError('Use a planar closed profile without self-intersections') from None
        if not face.isValid() or face.Area<=1e-9 or not isinstance(face.Surface,Part.Plane):raise ValueError('Use one planar closed profile without holes')
    else:
        if w.isClosed() or len(w.Edges)!=1 or w.Orientation!='Forward' or w.Edges[0].Orientation!='Forward':raise ValueError('Use one open forward edge for path and guide;no chains or closed paths')
        curve=w.Edges[0].Curve
        if isinstance(curve,(Part.BSplineCurve,Part.BezierCurve)) and (curve.NbPoles>50 or (hasattr(curve,'isPeriodic') and curve.isPeriodic())):raise ValueError('Path/guide spline must be nonperiodic with at most50 poles')
        if not isinstance(curve,(Part.Line,Part.Circle,Part.BSplineCurve,Part.BezierCurve)):raise ValueError('Path and guide support line,circular arc,Bezier or BSpline only')
    return w

def sampled(edge,fraction):
    u=edge.FirstParameter if fraction==0 else edge.LastParameter if fraction==1 else edge.getParameterByLength(edge.Length*fraction)
    return edge.valueAt(u),edge.tangentAt(u)

def shape(profile,path,rail):
    checked(profile.Document if profile else None,profile,path,rail)
    section=wire(profile,True);spine=wire(path);guide=wire(rail);pe=spine.Edges[0];ge=guide.Edges[0];face=Part.Face(section)
    start,tangent=sampled(pe,0);gstart,_=sampled(ge,0);end,etangent=sampled(pe,1);gend,_=sampled(ge,1)
    if face.distToShape(Part.Vertex(start))[0]>1e-6 or section.distToShape(Part.Vertex(gstart))[0]>1e-6:raise ValueError('Place path start inside the profile and guide start on its boundary')
    if abs(abs(face.normalAt(0,0).dot(tangent))-1)>1e-7:raise ValueError('Profile plane must be perpendicular to the path start tangent')
    if abs((gend-end).dot(etangent))>1e-6:raise ValueError('Guide end must lie in the path end normal plane')
    if spine.distToShape(guide)[0]<=1e-6:raise ValueError('Path and guide must remain separated by more than1e-6mm')
    for i in range(65):
        point,tangent=sampled(pe,i/64);q,_=sampled(ge,i/64);guide_normal(tuple(tangent),tuple(q-point))
    try:
        maker=Part.BRepOffsetAPI.MakePipeShell(spine);maker.setTolerance(1e-7,1e-7,1e-7);maker.setMaxDegree(9);maker.setMaxSegments(100)
        maker.setAuxiliarySpine(guide,True,0);maker.add(section,False,False)
        if not maker.isReady():raise ValueError('Native guided sweep is not ready')
        maker.build()
        if not maker.makeSolid():raise ValueError('Native guided sweep cannot be solidified')
        result=maker.shape()
    except (Part.OCCError,RuntimeError) as error:raise ValueError('Native guided sweep failed: '+str(error)) from None
    if result.isNull() or not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:raise ValueError('Guided sweep did not produce one valid solid')
    box=result.BoundBox
    if any(not math.isfinite(v) or abs(v)>1e6 for v in (box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax)):raise ValueError('Guided sweep bounds exceed +/-1000000mm')
    return Part.makeCompound([result])

def signature(profile,path,rail,existing=None):
    checked(profile.Document if profile else None,profile,path,rail,existing)
    def stamp(s):return (s.Name,s.Shape.hashCode(),str(s.getGlobalPlacement()),tuple(s.State),str(getattr(s,'Error','')))
    return (tuple(stamp(s) for s in (profile,path,rail)),tuple(hierarchy([profile,path,rail])),tuple((s.Name,tuple(s.State),str(getattr(s,'Error',''))) for source in (profile,path,rail) for s in source.OutListRecursive),None if existing is None else (stamp(existing),existing.Profile.Name,existing.Path.Name,existing.GuideRail.Name,tuple(existing.SourceHierarchy)))

class GuidedSweep:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            inputs=[obj.Profile,obj.Path,obj.GuideRail];checked(obj.Document,*inputs,obj)
            if hierarchy(inputs)!=list(obj.SourceHierarchy):raise ValueError('Input hierarchy changed;reselect inputs')
            out=shape(*inputs);obj.Shape=out;obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass
class ViewProvider:
    def __init__(self,vo):vo.Proxy=self
    def doubleClicked(self,vo):
        import FreeCADGui as Gui,guided_sweep_ui
        guided_sweep_ui.show(Gui.fluxcad_workspace,vo.Object);return True
    def dumps(self):return None
    def loads(self,state):pass

def apply(profile,path,rail,existing=None,expected=None):
    doc=profile.Document if profile else None;checked(doc,profile,path,rail,existing)
    if expected is not None and signature(profile,path,rail,existing)!=expected:raise ValueError('Inputs changed;close and reopen')
    from model_features import placed_preview,verify_result
    preview=placed_preview(shape(profile,path,rail),existing)
    downstream={o.Name:tuple(bool(getattr(o.Shape,n)) for n in ('Solids','Faces','Edges')) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    with model.transaction(doc,'Sweep with Guide Rail'):
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','GuidedSweep')
            for typ,n in [('App::PropertyBool','FluxGuidedSweep'),('App::PropertyLinkGlobal','Profile'),('App::PropertyLinkGlobal','Path'),('App::PropertyLinkGlobal','GuideRail'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','SourceHierarchy'),('App::PropertyString','Error')]:obj.addProperty(typ,n,'GuidedSweep')
            obj.FluxGuidedSweep=True;GuidedSweep(obj);ViewProvider(obj.ViewObject)
            for n in ('FluxGuidedSweep','Profile','Path','GuideRail','SourceContainers','SourceHierarchy'):obj.setEditorMode(n,2)
            obj.setEditorMode('Error',1)
        obj.Profile=profile;obj.Path=path;obj.GuideRail=rail;obj.SourceContainers=parents([profile,path,rail]);obj.SourceHierarchy=hierarchy([profile,path,rail]);obj.touch();doc.recompute()
        if obj.Error:raise ValueError(obj.Error)
        verify_result(obj,preview)
        for child in obj.InListRecursive:
            if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),downstream[child.Name]))))):raise ValueError('Later geometry would disappear;guided sweep edit cancelled')
        profile.Visibility=False;path.Visibility=False;rail.Visibility=False;obj.Visibility=True
    return obj

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={s.Name for s in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        members=self.previous.pop((changed.Document.Name,changed.Name),set())|{s.Name for s in changed.Group}
        for obj in changed.Document.Objects:
            if getattr(obj,'FluxGuidedSweep',False) and any(s and (s.Name in members or changed in containers(s) or changed in list(obj.SourceContainers)) for s in (obj.Profile,obj.Path,obj.GuideRail)):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={k:v for k,v in self.previous.items() if k[0]!=doc.Name}
old=getattr(App,'_fullarc_guided_observer',None)
if old is not None:App.removeDocumentObserver(old)
App._fullarc_guided_observer=HierarchyObserver();App.addDocumentObserver(App._fullarc_guided_observer)
