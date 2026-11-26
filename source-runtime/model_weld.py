"""Manual native TechDraw leader/weld/tile objects,printed-mm coordinates."""
from pathlib import Path
import FreeCAD as App
import drawing,model,model_balloon
from weld_values import validate_text,validate_point
KINDS={'Fillet':'fillet','Square':'Square','V':'V'}
def symbol_file(kind,other=False):
    if type(kind) is not str or kind not in KINDS:raise ValueError('Choose Fillet,Square or V weld')
    path=Path(App.getResourceDir())/'Mod/TechDraw/Symbols/Welding/AWS'/(KINDS[kind]+('Down.svg' if other else 'Up.svg'))
    if not path.is_file():raise ValueError('Native welding symbol resource is missing')
    return str(path)
def tiles(weld):return sorted([x for x in weld.InList if x.TypeId=='TechDraw::DrawTileWeld' and x.TileParent==weld],key=__import__('builtins')._fullarc_qt_slot(lambda x:-x.TileRow,(1, 1, False, False)))
def check(weld):
    if not weld or weld.TypeId!='TechDraw::DrawWeldSymbol' or not getattr(weld,'FluxWeld',False):raise ValueError('Select a FullArcCAD welding symbol')
    line=weld.Leader
    if not line or not getattr(line,'FluxWeldLeader',False) or line.TypeId!='TechDraw::DrawLeaderLine' or len(tiles(weld))!=2:raise ValueError('Weld leader/tiles missing')
    return line
def settings(weld):
    line=check(weld);tip=(float(line.X),float(line.Y));points=tuple((tip[0]+v.x,tip[1]-v.y) for v in line.WayPoints);a,o=tiles(weld)
    return dict(kind=str(weld.WeldType),points=points,left=a.LeftText,center=a.CenterText,right=a.RightText,tail=weld.TailText,both=bool(o.SymbolFile),around=bool(weld.AllAround),field=bool(weld.FieldWeld))
def signature(view,existing=None):
    stamp=model_balloon.signature(view)
    if existing:
        line=check(existing);page=drawing.page_of(view)
        if line.LeaderParent!=view or line not in page.Views or existing not in page.Views or line.Scalable or line.AutoHorizontal:raise ValueError('Weld reference or line mode changed')
        if any(x.ExpressionEngine for x in [line,existing]+tiles(existing)):raise ValueError('Remove weld coordinate/text expressions before editing')
        a,o=tiles(existing)
        if a.TileRow!=0 or o.TileRow!=-1:raise ValueError('Native weld tile rows changed')
        return stamp+(existing.Name,line.Name,settings(existing),a.SymbolFile,o.SymbolFile)
    return stamp
def apply(view,kind='Fillet',points=((0.,0.),(15.,15.),(35.,15.)),left='',center='',right='',tail='',both=False,around=False,field=False,existing=None,expected=None):
    if type(points) not in (tuple,list) or len(points)!=3:raise ValueError('Specify three leader points')
    points=tuple(validate_point(p) for p in points)
    if any((App.Vector(*points[i],0)-App.Vector(*points[i+1],0)).Length<=1e-6 for i in (0,1)) or abs(points[1][1]-points[2][1])>1e-7:raise ValueError('Use two nonzero leader segments with a horizontal final segment')
    left,center,right,tail=(validate_text(x) for x in (left,center,right,tail))
    if any(type(x) is not bool for x in (both,around,field)):raise ValueError('Weld flags require bool')
    upper=symbol_file(kind);lower=symbol_file(kind,True) if both else '';stamp=signature(view,existing)
    if expected is not None and stamp!=expected:raise ValueError('Inputs changed;close and reopen')
    page=model_balloon.target(view);doc=view.Document
    with model.transaction(doc,'Welding Symbol'):
        if existing:weld=existing;line=check(weld)
        else:
            line=doc.addObject('TechDraw::DrawLeaderLine','WeldLeader');line.LeaderParent=view;page.addView(line);line.addProperty('App::PropertyBool','FluxWeldLeader');line.FluxWeldLeader=True;line.setEditorMode('FluxWeldLeader',2)
            weld=doc.addObject('TechDraw::DrawWeldSymbol','WeldingSymbol');weld.Leader=line;page.addView(weld);weld.addProperty('App::PropertyBool','FluxWeld');weld.FluxWeld=True;weld.setEditorMode('FluxWeld',2);weld.addProperty('App::PropertyString','WeldType');weld.setEditorMode('WeldType',1)
        line.X,line.Y=points[0];line.WayPoints=[App.Vector(x-points[0][0],-(y-points[0][1]),0) for x,y in points];line.Scalable=False;line.AutoHorizontal=False;line.RotatesWithParent=False;line.StartSymbol='Filled arrow';line.EndSymbol='None'
        weld.WeldType=kind;weld.AllAround=around;weld.FieldWeld=field;weld.AlternatingWeld=False;weld.TailText=tail
        a,o=tiles(weld);a.TileRow=0;o.TileRow=-1;a.SymbolFile=upper;o.SymbolFile=lower
        a.LeftText=left;a.CenterText=center;a.RightText=right
        o.LeftText=left if both else '';o.CenterText=center if both else '';o.RightText=right if both else ''
        doc.recompute()
        if any('Invalid' in x.State or 'Error' in x.State for x in [line,weld,a,o]):raise ValueError('Native weld symbol failed')
        actual=settings(weld);actual_points=actual.pop('points')
        if len(actual_points)!=3 or any(abs(actual_points[i][j]-points[i][j])>1e-9 for i in range(3) for j in range(2)):raise ValueError('Native weld coordinates changed')
        if actual!=dict(kind=kind,left=left,center=center,right=right,tail=tail,both=both,around=around,field=field):raise ValueError('Native weld parameters changed')
    return weld
