"""Linked whole-surface stitching with an automatic shell/solid result."""
import FreeCAD as App
import Part
import model
from i18n import tr
from stitch_geometry import build

def parents(sources):
    result=[]
    for source in sources:
        parent=source.getParentGeoFeatureGroup()
        while parent and parent not in result:
            result.append(parent);parent=parent.getParentGeoFeatureGroup()
    return result

def checked(doc,sources,existing=None):
    sources=list(sources)
    if not sources or len({o.Name for o in sources})!=len(sources):
        raise ValueError(tr('縫合するサーフェスを重複なく選択してください。','Select surfaces without duplicates.'))
    for source in sources:
        if source.Document!=doc or doc.getObject(source.Name)!=source or (existing and (source==existing or existing in source.OutListRecursive)):
            raise ValueError(tr('同じ文書内の独立したサーフェスを選択してください。','Select independent surfaces in the same document.'))
        if any('Invalid' in obj.State or getattr(obj,'Error','') for obj in [source]+source.OutListRecursive):
            raise ValueError(tr('参照元のエラーを修正してください。','Fix the source error first.'))
    return sources

def shape(sources):
    try:return build([model.world_shape(source) for source in sources])
    except (ValueError,RuntimeError,Part.OCCError) as error:
        raise ValueError(tr('面全体を選び、一続きの殻になる境界を確認してください。隙間や重複した面は縫合できません。','Select whole surfaces forming one connected shell. Gaps or duplicate faces cannot be stitched.')+'\n'+str(error)) from error

def preview(doc,sources,existing=None):
    result=shape(checked(doc,sources,existing))
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result

class Stitch:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            sources=checked(obj.Document,obj.Sources,obj)
            if parents(sources)!=list(obj.SourceContainers):
                raise ValueError(tr('参照元の階層が変わりました。このコマンドで選び直してください。','The source hierarchy changed. Reselect sources with this command.'))
            result=shape(sources)
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.ResultSolid=bool(result.Solids);obj.Error=''
        except Exception as error:obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass

def apply(doc,sources,existing=None):
    if existing and (existing.Document!=doc or not getattr(existing,'FluxStitch',False)):
        raise ValueError(tr('再編集する縫合を選択してください。','Select a stitch feature to edit.'))
    sources=checked(doc,sources,existing);expected=preview(doc,sources,existing)
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    visible=[(source,bool(source.Visibility)) for source in sources]
    try:
        with model.transaction(doc,tr('面を縫合','Stitch Surfaces')):
            obj=existing
            if obj is None:
                obj=doc.addObject('Part::FeaturePython','Stitch');obj.Label=tr('面の縫合','Stitch Surfaces')
                for typ,name in [('App::PropertyBool','FluxStitch'),('App::PropertyLinkListGlobal','Sources'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyBool','ResultSolid'),('App::PropertyString','Error')]:obj.addProperty(typ,name,'FluxCAD')
                obj.FluxStitch=True;obj.setEditorMode('FluxStitch',2);obj.setEditorMode('SourceContainers',2)
                for name in ('Sources','ResultSolid','Error'):obj.setEditorMode(name,1)
                Stitch(obj);obj.ViewObject.Proxy=0;obj.ViewObject.ShapeColor=(.72,.79,.85)
            obj.Sources=sources;obj.SourceContainers=parents(sources);doc.recompute();actual=model.world_shape(obj)
            area=max(1e-7,expected.Area*1e-7)
            if obj.Error or actual.isNull() or not actual.isValid() or len(actual.Faces)!=len(expected.Faces) or abs(actual.Area-expected.Area)>area or actual.common(expected).Area<expected.Area-area:
                raise ValueError(obj.Error or tr('プレビューと結果が一致しません。','Preview and result do not match.'))
            if bool(actual.Solids)!=bool(expected.Solids) or (expected.Solids and actual.cut(expected).Volume+expected.cut(actual).Volume>max(1e-7,expected.Volume*1e-7)):
                raise ValueError(tr('ソリッドの結果が一致しません。','Solid results do not match.'))
            for later in obj.InListRecursive:
                if 'Invalid' in later.State or getattr(later,'Error','') or (hasattr(later,'Shape') and (later.Shape.isNull() or not later.Shape.isValid() or (later.Name in downstream and not later.Shape.Solids))):
                    raise ValueError(tr('後続の加工が成立しないため変更を取り消しました。','The edit was cancelled because a later feature would become invalid.'))
            if not existing:
                for source in sources:source.Visibility=False
                obj.Visibility=True
        return obj
    except Exception:
        for source,state in visible:
            if source.Document:source.Visibility=state
        raise
