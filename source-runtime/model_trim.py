"""Linked trim with explicit region reselection after geometry/relative-pose changes."""
import hashlib
import FreeCAD as App
import Part
import model
from model_stitch import parents
from trim_geometry import pieces,trimmed
from trim_selection import kept_indices
from i18n import tr

def fingerprint(obj):
    shape=obj.Shape.copy();shape.Placement=App.Placement()
    return hashlib.sha256(shape.exportBrepToString().encode()).hexdigest()

def relative(source,tool):return tuple(source.getGlobalPlacement().inverse().multiply(tool.getGlobalPlacement()).toMatrix().A)

def checked(doc,source,tool,existing=None):
    if not source or not tool or source==tool:raise ValueError(tr('対象と切断面を別々に選んでください。','Select distinct target and tool surfaces.'))
    for obj in (source,tool):
        if obj.Document!=doc or doc.getObject(obj.Name)!=obj or (existing and (obj==existing or existing in obj.OutListRecursive)):
            raise ValueError(tr('同じ文書の独立した形状を選んでください。','Select independent shapes in the same document.'))
        if any('Invalid' in o.State or getattr(o,'Error','') for o in [obj]+obj.OutListRecursive):raise ValueError(tr('参照元のエラーを修正してください。','Fix the source error first.'))
    shape=source.Shape
    if shape.isNull() or not shape.isValid() or shape.Solids or len(shape.Faces)!=1 or len(shape.Edges)!=len(shape.Faces[0].Edges):
        raise ValueError(tr('対象は1枚の面にしてください。','The target must contain one face.'))
    if tool.Shape.isNull() or tool.Shape.ShapeType not in ('Face','Shell') or not tool.Shape.isValid():raise ValueError(tr('切断用の面または殻を選択してください。','Select a face or shell tool.'))

def regions(doc,source,tool,existing=None):
    checked(doc,source,tool,existing)
    try:return pieces(model.world_shape(source).Faces[0],model.world_shape(tool),source.getGlobalPlacement())
    except (RuntimeError,Part.OCCError,ValueError) as error:raise ValueError(tr('切断面が対象を分ける位置に配置してください。面の自動延長は行いません。','Position the tool so it splits the target. Surfaces are not extended automatically.')+'\n'+str(error)) from error

def check_reference(obj):
    checked(obj.Document,obj.Source,obj.Tool,obj)
    if len(obj.RelativePose)!=16 or fingerprint(obj.Source)!=obj.SourceStamp or fingerprint(obj.Tool)!=obj.ToolStamp or parents([obj.Source,obj.Tool])!=list(obj.SourceContainers) or any(abs(a-b)>1e-10 for a,b in zip(relative(obj.Source,obj.Tool),obj.RelativePose)):
        raise ValueError(tr('参照形状または相対配置が変わりました。領域を選び直してください。','Input geometry or relative placement changed. Reselect regions.'))

class Trim:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            check_reference(obj);parts=regions(obj.Document,obj.Source,obj.Tool,obj)
            if len(parts)!=obj.RegionCount:raise ValueError(tr('領域数が変わりました。選び直してください。','The region count changed. Reselect regions.'))
            result=trimmed(parts,list(obj.Keep));obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def preview(doc,source,tool,keep,existing=None):
    parts=regions(doc,source,tool,existing);result=trimmed(parts,keep)
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result

def apply(doc,source,tool,keep,existing=None):
    if existing and (existing.Document!=doc or not getattr(existing,'FluxTrim',False)):raise ValueError('Select a trim feature')
    parts=regions(doc,source,tool,existing);keep=kept_indices(keep,len(parts));result=trimmed(parts,keep);expected=result.copy()
    if existing:expected.Placement=existing.getGlobalPlacement().multiply(expected.Placement)
    downstream={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in existing.InListRecursive if hasattr(o,'Shape')} if existing else {}
    visibility=bool(source.Visibility)
    try:
        with model.transaction(doc,tr('面をトリム','Trim Surface')):
            obj=existing
            if obj is None:
                obj=doc.addObject('Part::FeaturePython','SurfaceTrim');obj.Label=tr('面トリム','Surface Trim')
                for typ,name in [('App::PropertyBool','FluxTrim'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkGlobal','Tool'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyString','SourceStamp'),('App::PropertyString','ToolStamp'),('App::PropertyFloatList','RelativePose'),('App::PropertyInteger','RegionCount'),('App::PropertyIntegerList','Keep'),('App::PropertyString','Error')]:obj.addProperty(typ,name,'FluxCAD')
                obj.FluxTrim=True;Trim(obj);obj.ViewObject.Proxy=0;obj.ViewObject.ShapeColor=(.80,.69,.49)
                for name in ('FluxTrim','SourceContainers','SourceStamp','ToolStamp','RelativePose'):obj.setEditorMode(name,2)
                for name in ('Source','Tool','RegionCount','Keep','Error'):obj.setEditorMode(name,1)
            obj.Source=source;obj.Tool=tool;obj.SourceContainers=parents([source,tool]);obj.SourceStamp=fingerprint(source);obj.ToolStamp=fingerprint(tool);obj.RelativePose=relative(source,tool);obj.RegionCount=len(parts);obj.Keep=list(keep)
            doc.recompute();actual=model.world_shape(obj);tol=max(1e-7,expected.Area*1e-7)
            if obj.Error or actual.isNull() or not actual.isValid() or actual.Solids or len(actual.Faces)!=len(expected.Faces) or abs(actual.Area-expected.Area)>tol or actual.common(expected).Area<expected.Area-tol:raise ValueError(obj.Error or tr('プレビューと結果が一致しません。','Preview and result do not match.'))
            for later in obj.InListRecursive:
                if 'Invalid' in later.State or getattr(later,'Error','') or (hasattr(later,'Shape') and (later.Shape.isNull() or not later.Shape.isValid())):raise ValueError(tr('後続の加工が成立しないため変更を取り消しました。','The edit was cancelled because a later feature would become invalid.'))
                if later.Name in downstream and any(old and not new for old,new in zip(downstream[later.Name],(bool(later.Shape.Solids),bool(later.Shape.Faces),bool(later.Shape.Edges)))):
                    raise ValueError(tr('後続の加工の形状が失われるため変更を取り消しました。','The edit was cancelled because later geometry would disappear.'))
            source.Visibility=False;obj.Visibility=True
        return obj
    except Exception:
        if source.Document:source.Visibility=visibility
        raise
