"""A native line/rich-annotation pair, in printed mm relative to a base view."""
import math
import FreeCAD as App
import drawing,model,model_balloon
from leader_values import values
from i18n import tr
LINE='TechDraw::DrawLeaderLine';NOTE='TechDraw::DrawRichAnno'


def center_value(center):
    if type(center) is not tuple or len(center)!=2:raise ValueError('Text center must be an XY tuple')
    result=[]
    for value in center:
        if type(value) not in (int,float):raise ValueError('Text center requires numbers')
        try:value=float(value)
        except OverflowError:raise ValueError('Text center overflow')
        if not math.isfinite(value) or abs(value)>1e6:raise ValueError('Text center must be within +/-1000000mm')
        result.append(value)
    return tuple(result)


def pair(obj):
    if not obj or obj.Document is not App.ActiveDocument:raise ValueError('Use the active document')
    if obj.TypeId==NOTE and getattr(obj,'FluxLeaderNote',False):note=obj;line=note.AnnoParent
    elif obj.TypeId==LINE and getattr(obj,'FluxLeaderLine',False):
        line=obj;notes=[o for o in obj.Document.Objects if o.TypeId==NOTE and getattr(o,'FluxLeaderNote',False) and o.AnnoParent==line]
        if len(notes)!=1:raise ValueError('Leader must have exactly one FullArcCAD note')
        note=notes[0]
    else:raise ValueError('Select a FullArcCAD leader note')
    if not line or line.TypeId!=LINE or not getattr(line,'FluxLeaderLine',False):raise ValueError('Missing leader')
    return line,note


def settings(obj):
    line,note=pair(obj);tip=(float(line.X),float(line.Y));wp=line.WayPoints
    if len(wp)!=3 or wp[0].Length>1e-9 or any(abs(v.z)>1e-9 for v in wp):raise ValueError('Use a three-point planar leader')
    pts=tuple((tip[0]+v.x,tip[1]-v.y) for v in wp)
    return note.PlainText,pts,(tip[0]+float(note.X),tip[1]+float(note.Y))


def signature(view,existing=None):
    stamp=model_balloon.signature(view)
    if existing:
        line,note=pair(existing);page=drawing.page_of(view)
        if line.LeaderParent!=view or note.AnnoParent!=line or line not in page.Views or note not in page.Views:raise ValueError('Leader note association changed')
        if line.ExpressionEngine or note.ExpressionEngine:raise ValueError('Remove leader/note expressions before editing')
        if line.Scalable or line.AutoHorizontal:raise ValueError('Use a non-scalable,manual leader')
        if note.AnnoText!=values(*settings(note)[:2])[2]:raise ValueError('Native rich formatting changed;use the native text editor')
        stamp+=(line.Name,note.Name,settings(note),note.AnnoText,str(line.StartSymbol),str(line.EndSymbol),float(note.MaxWidth),bool(note.ShowFrame))
    return stamp


def apply(view,text,points,center=(50.,15.),existing=None,expected=None):
    text,points,html=values(text,points);center=center_value(center);stamp=signature(view,existing)
    if expected is not None and expected!=stamp:raise ValueError(tr('参照が変わりました。開き直してください。','The reference changed. Reopen the dialog.'))
    page=model_balloon.target(view);doc=view.Document;tip=points[0]
    with model.transaction(doc,tr('引出線付き注記を編集','Edit Leader Note') if existing else tr('引出線付き注記を作成','Create Leader Note')):
        if existing:line,note=pair(existing)
        else:
            line=doc.addObject(LINE,'NoteLeader');line.LeaderParent=view;page.addView(line)
            line.addProperty('App::PropertyBool','FluxLeaderLine','FullArcCAD');line.FluxLeaderLine=True;line.setEditorMode('FluxLeaderLine',2)
            note=doc.addObject(NOTE,'LeaderNote');note.AnnoParent=line;page.addView(note)
            note.addProperty('App::PropertyBool','FluxLeaderNote','FullArcCAD');note.FluxLeaderNote=True;note.setEditorMode('FluxLeaderNote',2)
            note.addProperty('App::PropertyString','PlainText','FullArcCAD');note.setEditorMode('PlainText',1)
        line.X,line.Y=tip;line.WayPoints=[App.Vector(x-tip[0],-(y-tip[1]),0) for x,y in points]
        line.Scalable=False;line.AutoHorizontal=False
        if 'RotatesWithParent' in line.PropertiesList:line.RotatesWithParent=False
        line.StartSymbol='Filled arrow';line.EndSymbol='None'
        note.PlainText=text;note.AnnoText=html;note.X=center[0]-tip[0];note.Y=center[1]-tip[1];note.MaxWidth=40;note.ShowFrame=False
        if 'OriginCentered' in note.PropertiesList:note.OriginCentered=True
        doc.recompute()
        if any('Invalid' in o.State or 'Error' in o.State for o in (line,note)):raise ValueError('Native leader annotation failed')
        actual=settings(note)
        if actual[0]!=text or max(abs(actual[1][i][j]-points[i][j]) for i in range(3) for j in range(2))>1e-9 or max(abs(actual[2][i]-center[i]) for i in range(2))>1e-9:raise ValueError('Native leader values changed')
    return note
