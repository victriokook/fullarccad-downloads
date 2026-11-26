"""Native loft and sweep features driven by whole, single-wire sketches."""
from i18n import tr
import Part
import model
from closed_loft_options import validate as validate_closed
from loft_point_options import validate_points
import math
from sweep_fraction_values import resolve_fraction
from sweep_backward_values import resolve_backward
from model_features import solid, placed_preview, verify_result


def wire(obj, profile=True):
    shape = model.world_shape(obj)
    if (shape.isNull() or not shape.isValid() or shape.Solids or len(shape.Wires)!=1
            or len(shape.Wires[0].Edges)!=len(shape.Edges)):
        raise ValueError(tr('%s：つながった輪郭が1つだけのスケッチを指定してください。')%obj.Label)
    result = shape.Wires[0]
    if profile:
        if not result.isClosed():
            raise ValueError(tr('%s：断面の輪郭を閉じてください。')%obj.Label)
        face = Part.Face(result)
        if not face.isValid() or face.Area<=1e-9:
            raise ValueError(tr('%s：断面の重複・自己交差を取り除いてください。')%obj.Label)
    return result


def point_section(obj):
    if obj is None or obj.Document is None or obj.Document.getObject(obj.Name) != obj or obj.isDerivedFrom('App::Link'):
        raise ValueError(tr('現在文書の独立した点を指定してください。','Select a live non-Link point object.'))
    if any('Invalid' in x.State or 'Error' in x.State or bool(getattr(x,'Error','')) for x in [obj]+list(obj.OutListRecursive)):
        raise ValueError(tr('点の参照元が無効です。','The point source is invalid.'))
    shape=model.world_shape(obj)
    if shape.isNull() or not shape.isValid() or shape.ShapeType not in ('Vertex','Compound') or len(shape.Vertexes)!=1 or shape.Edges or shape.Faces:
        raise ValueError(tr('全体が1頂点だけの点を指定してください。','Select a whole object containing exactly one vertex.'))
    if shape.ShapeType=='Compound' and (len(shape.childShapes())!=1 or shape.childShapes()[0].ShapeType!='Vertex'):
        raise ValueError(tr('余分な要素のない単一頂点を指定してください。','Use one vertex with no extra elements.'))
    v=shape.Vertexes[0]
    if any(not math.isfinite(x) or abs(x)>1e6 for x in v.Point):
        raise ValueError(tr('点座標は各軸±1000000mm以内にしてください。','Point coordinates must be within ±1000000mm per axis.'))
    return v


def is_point_section(obj):
    try:point_section(obj);return True
    except Exception:return False


def loft_shape(sections, ruled=False, closed=False, surface=False):
    if type(surface) is not bool:raise ValueError('Invalid loft output mode')
    if surface:
        import model_surface_loft
        return model_surface_loft.shape(sections,ruled,closed)
    try:validate_closed(closed,len(sections))
    except ValueError:
        raise ValueError(tr("閉ループは3～50断面、通常ロフトは2断面以上を指定してください。","Use 3–50 sections for a closed loop, or at least 2 for an open loft.")) from None
    if len(sections)<2:
        raise ValueError(tr('つなぐ順番に、断面スケッチを2つ以上追加してください。'))
    if len(set(sections))!=len(sections):
        raise ValueError(tr('同じ断面は繰り返し指定できません。'))
    wires=[];kinds=[]
    for obj in sections:
        shape=model.world_shape(obj)
        if not shape.Edges and not shape.Faces and shape.Vertexes:
            wires.append(point_section(obj));kinds.append('point')
        else:
            wires.append(wire(obj));kinds.append('wire')
    if 'point' in kinds:
        try:validate_points(kinds,closed)
        except ValueError:
            raise ValueError(tr('点は通常ロフトの最初・最後だけに指定できます。閉輪郭を1つ以上、合計2～50断面で指定してください。','Points are allowed only at open loft endpoints. Use at least one closed wire and 2–50 sections.')) from None
    try:
        result = solid(Part.makeLoft(wires,True,ruled,closed,5))
        if len(result.Solids)!=1:raise ValueError('separated solids')
        return result
    except (RuntimeError,ValueError):
        raise ValueError(tr('この断面ではロフトを作成できません。断面の位置・順序・輪郭を確認してください。')) from None


def sweep_shape(profile, path, frenet=False, transition=1, path_fraction=None, backward_fraction=None):
    fraction=resolve_fraction(path_fraction)
    backward=resolve_backward(backward_fraction)
    if fraction!=1 or backward!=0:
        import model_partial_sweep
        return model_partial_sweep.shape(profile,path,frenet,transition,fraction,backward)
    if not profile or not path:
        raise ValueError(tr('断面と経路のスケッチを指定してください。'))
    if profile==path:
        raise ValueError(tr('断面と経路は別々のスケッチを指定してください。'))
    if transition not in (0,1,2):
        raise ValueError(tr('角のつなぎ方を選択してください。'))
    section = wire(profile)
    spine = wire(path,False)
    try:
        result = solid(spine.makePipeShell([section],True,frenet,transition))
        if len(result.Solids)!=1:raise ValueError('separated solids')
        return result
    except (RuntimeError,ValueError):
        raise ValueError(tr('この断面と経路ではスイープを作成できません。断面を経路の端に配置し、経路の接続や曲がりを確認してください。')) from None


def sources(obj):
    sections = list(getattr(obj,'FluxSections',obj.Sections))
    path = getattr(obj,'FluxPath',None)
    if path is None and obj.TypeId=='Part::Sweep':path=obj.Spine[0]
    return sections,path


def create(doc, kind, sections, path=None, ruled=False, frenet=False, transition=1, existing=None, closed=False, path_fraction=None, backward_fraction=None, surface=None):
    if kind not in ('loft','sweep'):raise ValueError(tr('作成方法を選択してください。'))
    if surface is None:surface=bool(getattr(existing,'FluxSurfaceLoft',False))
    if type(surface) is not bool:raise ValueError('Invalid loft output mode')
    if surface:
        if kind!='loft':raise ValueError('Surface output is available for Loft only')
        import model_surface_loft
        return model_surface_loft.create(doc,sections,ruled,closed,existing)
    if getattr(existing,'FluxSurfaceLoft',False):raise ValueError('Create a new solid loft;surface loft cannot change representation')
    if kind=='sweep':
        fraction=resolve_fraction(path_fraction,float(getattr(existing,'PathFraction',1)) if existing else 1)
        backward=resolve_backward(backward_fraction,float(getattr(existing,'BackwardFraction',0)) if existing else 0)
        if getattr(existing,'FluxPartialSweep',False) or fraction!=1 or backward!=0:
            if len(sections)!=1:raise ValueError('Select one sweep profile')
            import model_partial_sweep
            return model_partial_sweep.create(doc,sections[0],path,frenet,transition,fraction,existing,backward)
    if kind=='loft' and (getattr(existing,'FluxPointLoft',False) or any(is_point_section(o) for o in sections)):
        import model_point_loft
        return model_point_loft.create(doc,sections,ruled,closed,existing)
    inputs = list(sections)+([path] if path is not None else [])
    if (any(obj.Document!=doc for obj in inputs) or (existing and existing.Document!=doc)):
        raise ValueError(tr('同じ文書内のスケッチを指定してください。'))
    if existing and any(obj==existing or existing in obj.OutListRecursive for obj in inputs):
        raise ValueError(tr('この加工に依存する形状は断面・経路に指定できません。'))
    if kind=='sweep' and len(sections)!=1:
        raise ValueError(tr('スイープの断面を1つ指定してください。'))
    shape = loft_shape(sections,ruled,closed) if kind=='loft' else sweep_shape(sections[0],path,frenet,transition)
    expected = placed_preview(shape,existing)
    title = tr('ロフト') if kind=='loft' else tr('スイープ')
    dimensions = {f.Name:tuple(len(getattr(f.Shape,n)) for n in ('Solids','Faces','Edges')) for f in existing.InListRecursive if hasattr(f,'Shape')} if existing and kind=='loft' else {}
    with model.transaction(doc,title+(tr('を編集') if existing else '')):
        previous = {}
        if existing:
            old_sections,old_path = sources(existing)
            previous.update(zip(old_sections,existing.Sections))
            if old_path:previous[old_path]=existing.Spine[0]
        def reference(source):
            return previous[source] if source in previous else model._world_source(doc,source)
        refs = [reference(source) for source in sections]
        path_ref = reference(path) if path else None
        obj = existing
        if obj is None:
            obj = doc.addObject('Part::Loft' if kind=='loft' else 'Part::Sweep','Loft' if kind=='loft' else 'Sweep')
            obj.Label = title
            obj.addProperty('App::PropertyBool','FluxLoft' if kind=='loft' else 'FluxSweep','FluxCAD')
            setattr(obj,'FluxLoft' if kind=='loft' else 'FluxSweep',True)
            obj.addProperty('App::PropertyLinkListGlobal','FluxSections','FluxCAD')
            if kind=='sweep':obj.addProperty('App::PropertyLinkGlobal','FluxPath','FluxCAD')
            for name in ('FluxLoft','FluxSweep','FluxSections','FluxPath'):
                if name in obj.PropertiesList:obj.setEditorMode(name,2)
        obj.Sections = refs
        obj.FluxSections = list(sections)
        obj.Solid = True
        if kind=='loft':
            obj.Ruled = ruled
            obj.Closed = closed
            obj.MaxDegree = 5
        else:
            obj.Spine = (path_ref,[])
            obj.FluxPath = path
            obj.Frenet = frenet
            obj.Transition = transition
        verify_result(obj,expected)
        for name,counts in dimensions.items():
            dependent=doc.getObject(name)
            if dependent is None or any(old and not len(getattr(dependent.Shape,n)) for n,old in zip(("Solids","Faces","Edges"),counts)):
                raise ValueError(tr("後の加工を更新できないため、変更を取り消しました。","A dependent feature lost its geometry. The edit was cancelled."))
        for source in inputs+refs+([path_ref] if path_ref else []):source.Visibility=False
        if not existing:obj.Visibility=True
        for old in set(previous.values())-set(refs)-{path_ref}:
            if getattr(old,'FluxCADInternal',False) and not old.InList:doc.removeObject(old.Name)
    return obj
