"""Linked directional projection; all intersection branches retained."""
import FreeCAD as App
import Part
import model
from model_stitch import parents
from projection_geometry import projected
from projection_direction import direction


def checked(doc, source, target, existing=None):
    if source == target:
        raise ValueError("Choose distinct curve and surface objects")
    for obj in (source, target):
        if obj is None or obj.Document != doc or doc.getObject(obj.Name) != obj:
            raise ValueError("Choose inputs in the same document")
        if existing and (obj == existing or existing in obj.OutListRecursive):
            raise ValueError("Cyclic projection reference")
        if any("Invalid" in o.State or getattr(o,"Error","") for o in [obj] + obj.OutListRecursive):
            raise ValueError("Repair input errors first")


def shape(source, target, local_direction):
    vector = source.getGlobalPlacement().Rotation.multVec(App.Vector(*direction(local_direction)))
    return projected(model.world_shape(source), model.world_shape(target), (vector.x, vector.y, vector.z))


def preview(doc, source, target, local_direction, existing=None):
    checked(doc, source, target, existing)
    out = shape(source, target, local_direction)
    if existing:
        out.Placement = existing.getGlobalPlacement().multiply(out.Placement)
    return out


class Projection:
    def __init__(self, obj): obj.Proxy = self
    def execute(self, obj):
        pose = App.Placement(obj.Placement)
        try:
            checked(obj.Document, obj.Source, obj.Target, obj)
            if parents([obj.Source,obj.Target]) != list(obj.SourceContainers):
                raise ValueError("Input hierarchy changed; reselect inputs")
            v = obj.Direction
            out = shape(obj.Source, obj.Target, (v.x,v.y,v.z))
            obj.Shape = Part.makeCompound([out]); obj.Placement = pose; obj.Error = ""
        except Exception as error:
            obj.Shape = Part.Shape(); obj.Placement = pose; obj.Error = str(error)
    def dumps(self): return None
    def loads(self, state): pass


def apply(doc, source, target, local_direction, existing=None):
    if existing and (existing.Document != doc or not getattr(existing,"FluxProjection",False)):
        raise ValueError("Choose a projection feature to edit")
    local_direction = direction(local_direction)
    expected = preview(doc, source, target, local_direction, existing)
    downstream = {o.Name:(bool(o.Shape.Edges),bool(o.Shape.Faces),bool(o.Shape.Solids)) for o in existing.InListRecursive if hasattr(o,"Shape")} if existing else {}
    with model.transaction(doc,"Project to Surface"):
        obj = existing
        if obj is None:
            obj = doc.addObject("Part::FeaturePython","SurfaceProjection")
            for typ,name in [("App::PropertyBool","FluxProjection"),("App::PropertyLinkGlobal","Source"),("App::PropertyLinkGlobal","Target"),("App::PropertyLinkListGlobal","SourceContainers"),("App::PropertyVector","Direction"),("App::PropertyString","Error")]:obj.addProperty(typ,name,"FluxCAD")
            obj.FluxProjection=True; obj.setEditorMode("FluxProjection",2); obj.setEditorMode("SourceContainers",2)
            for name in ("Source","Target","Direction","Error"):obj.setEditorMode(name,1)
            Projection(obj); obj.ViewObject.Proxy=0
        obj.Source=source;obj.Target=target;obj.SourceContainers=parents([source,target]);obj.Direction=App.Vector(*local_direction)
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
