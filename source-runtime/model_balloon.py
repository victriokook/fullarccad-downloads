"""Manual numeric circular balloons using native TechDraw document objects."""
import math
import FreeCAD as App
import drawing,model
from balloon_values import values
from i18n import tr

TYPE='TechDraw::DrawViewBalloon'


def target(view):
    doc=App.ActiveDocument
    if not doc or not view or view.Document is not doc or view.TypeId!=drawing.VIEW:
        raise ValueError(tr('現在の図面の単独投影図を選択してください。','Select a base drawing view in the active document.'))
    page=drawing.page_of(view)
    if not page or not page.Template or not view.Source:
        raise ValueError(tr('用紙と元形状を持つ投影図を選択してください。','Select a view with a page and source geometry.'))
    for obj in [view,page]+list(view.Source):
        if obj.Document is not doc or 'Invalid' in obj.State or 'Error' in obj.State or 'Touched' in obj.State or getattr(obj,'AssemblyError',''):
            raise ValueError(tr('図面または元形状にエラーがあります。','The drawing or source geometry has an error.'))
    for source in view.Source:
        if source.TypeId=='App::Link' or not hasattr(source,'Shape') or source.Shape.isNull() or not source.Shape.isValid():
            raise ValueError(tr('有効な同一文書の元形状が必要です。','Valid source geometry in the same document is required.'))
    scale=float(view.Scale)
    if not math.isfinite(scale) or not .001<=scale<=1000:raise ValueError('View scale must be 0.001..1000')
    return page


def signature(view,existing=None):
    page=target(view)
    result=(view.Document.Name,view.Name,page.Name,tuple(v.Name for v in page.Views),float(view.X),float(view.Y),float(view.Scale),str(view.ScaleType),float(view.Rotation),tuple(view.Direction),tuple(view.XDirection),str(page.Template.Template),
            tuple((o.Name,o.Shape.exportBrepToString(),tuple(o.getGlobalPlacement().toMatrix().A),o.Label) for o in view.Source))
    if existing:
        if existing.Document is not view.Document or existing.TypeId!=TYPE or not getattr(existing,'FluxBalloon',False) or existing.SourceView!=view or drawing.page_of(existing)!=page:
            raise ValueError(tr('編集するバルーンの参照を確認してください。','Check the balloon reference before editing.'))
        if any(name in ('Text','OriginX','OriginY','X','Y') for name,expression in existing.ExpressionEngine):
            raise ValueError(tr('バルーンの座標式を解除してから編集してください。','Remove balloon coordinate expressions before editing.'))
        result+=(existing.Name,existing.Text,float(existing.OriginX),float(existing.OriginY),float(existing.X),float(existing.Y),str(existing.BubbleShape),float(existing.KinkLength))
    return result


def settings(obj):
    if obj.TypeId!=TYPE or not getattr(obj,'FluxBalloon',False):raise ValueError('Select a FullArcCAD balloon')
    if not obj.Text.isascii() or not obj.Text.isdigit():raise ValueError('Balloon text is not a numeric item')
    return (int(obj.Text),float(obj.OriginX),float(obj.OriginY),float(obj.X),float(obj.Y))


def apply(view,number,origin_x,origin_y,bubble_x,bubble_y,existing=None,expected=None):
    text,ox,oy,x,y=values(number,origin_x,origin_y,bubble_x,bubble_y)
    stamp=signature(view,existing)
    if expected is not None and stamp!=expected:raise ValueError(tr('参照が変わりました。開き直してください。','The reference changed. Reopen the dialog.'))
    page=target(view);doc=view.Document
    with model.transaction(doc,tr('部品番号バルーンを編集','Edit Item Balloon') if existing else tr('部品番号バルーンを作成','Create Item Balloon')):
        obj=existing or doc.addObject(TYPE,'ItemBalloon')
        if not existing:
            obj.addProperty('App::PropertyBool','FluxBalloon','FullArcCAD');obj.FluxBalloon=True;obj.setEditorMode('FluxBalloon',2)
            obj.SourceView=view;page.addView(obj)
        obj.Text=text;obj.OriginX=ox;obj.OriginY=oy;obj.X=x;obj.Y=y
        obj.BubbleShape='Circular';obj.KinkLength=0
        doc.recompute()
        if 'Invalid' in obj.State or 'Error' in obj.State or obj.SourceView!=view or obj not in page.Views:
            raise ValueError('Native balloon creation failed')
        if settings(obj)!=(number,ox,oy,x,y):raise ValueError('Native balloon values changed')
    return obj
