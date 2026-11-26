"""Dimensioned spheres, ring tori, round-wire coils and hollow pipes."""
import math
import FreeCAD as App
import Part
import model
import model_sections
import model_dome
from pipe_wall import wall_value
import pipe_path_guard
import pipe_polygon
import pipe_path_prefix
import pipe_path_span
from pipe_two_sided_values import fractions
from pipe_path_fraction_values import effective_fraction
import coil_sections
import coil_taper
import planar_spiral
from i18n import tr

KINDS=('sphere','torus','coil','spiral','pipe','dome')


def title(kind):
    return {'dome':tr('ドーム','Dome'),'sphere':tr('球','Sphere'),'torus':tr('トーラス','Torus'),
            'spiral':tr('平面スパイラル','Planar Spiral'),'coil':tr('コイル','Coil'),'pipe':tr('パイプ','Pipe')}[kind]


def defaults(kind):
    return dict(dome=dict(width=60,depth=40,height=15,thickness=0),sphere=dict(diameter=20),torus=dict(diameter=30,section=6),
                coil=dict(diameter=30,section=3,pitch=6,turns=4,left=False,section_kind="circular",taper_angle=0),
                spiral=dict(diameter=30,section=2,growth=6,turns=3,left=False,section_kind="circular"),
                pipe=dict(diameter=10,wall=1,length=30,path=None,section_kind="circular",path_fraction=1,backward_fraction=0))[kind].copy()


def settings(obj):
    kind=obj.FluxPrimitive
    if kind=='dome':return model_dome.settings(obj)
    if kind=='sphere':return dict(diameter=obj.Radius.Value*2)
    if kind=='torus':return dict(diameter=obj.Radius1.Value*2,section=obj.Radius2.Value*2)
    if kind=='spiral':return dict(diameter=obj.Diameter.Value,section=obj.Section.Value,growth=obj.Growth.Value,turns=obj.Turns,left=obj.LeftHanded,section_kind=str(obj.CoilSection))
    if kind=='coil':return dict(diameter=obj.Diameter.Value,section=obj.Section.Value,
                                pitch=obj.Pitch.Value,turns=obj.Turns,left=obj.LeftHanded,
                                section_kind=str(getattr(obj,"CoilSection","circular")),
                                taper_angle=float(getattr(obj,"TaperAngle",0)))
    return dict(diameter=obj.Diameter.Value,wall=obj.Wall.Value,length=obj.Length.Value,path=obj.FluxPath,section_kind=str(getattr(obj,'PipeSection','circular')),path_fraction=float(getattr(obj,'PathFraction',1)),backward_fraction=float(getattr(obj,'BackwardFraction',0)))


def number(value,label,minimum=.001,maximum=100000):
    value=float(value)
    if not math.isfinite(value) or not minimum<=value<=maximum:
        raise ValueError(tr('%s：%g～%g の値を指定してください。','%s: enter a value from %g to %g.')%(label,minimum,maximum))
    return value


def validate(kind,values):
    if kind=='dome':return model_dome.validate(values)
    if kind not in KINDS:raise ValueError('Unknown primitive: '+str(kind))
    result=defaults(kind)
    if set(values)-set(result):raise ValueError('Unknown primitive parameters')
    result.update(values)
    if kind=='pipe':
        result['path_fraction']=effective_fraction(result['path_fraction'],result['path'] is not None)
        result['path_fraction'],result['backward_fraction']=fractions(result['path_fraction'],result['backward_fraction'],result['path'] is not None)
        if result['backward_fraction'] and not model_sections.wire(result['path'],False).isClosed():raise ValueError('Backward fraction requires a closed path')
        if type(result['section_kind']) is not str or result['section_kind'] not in ('circular','square','triangle'):raise ValueError('Unknown pipe section')
        result['wall']=wall_value(result['diameter'],result['wall'])
        if result['section_kind']!='circular':pipe_polygon.inner_side(result['section_kind'],result['diameter'],result['wall'])
    for key in set(result)-{'left','path','section_kind','taper_angle','path_fraction','backward_fraction'}:
        result[key]=number(result[key],key,.25 if key=='turns' else 0 if kind=='pipe' and key=='wall' else .001,50 if key=='turns' else 100000)
    if kind in ('torus','coil','spiral') and result['section']>=result['diameter']:
        raise ValueError(tr('断面の直径は中心径より小さくしてください。','Section diameter must be smaller than the centerline diameter.'))
    if kind=='coil':
        result['taper_angle']=number(result['taper_angle'],'Taper angle',-45,45)
        height=number(result['pitch']*result['turns'],tr('コイルの高さ','Coil height'))
        end_radius=coil_taper.taper_radius(result['diameter']/2,height,result['taper_angle'])
        min_radius=min(result['diameter']/2,end_radius)
        section_kind=result['section_kind']
        bound=result['section']/2 if section_kind=='circular' else coil_sections.section_bound(section_kind,result['section'])
        if bound>=min_radius:
            raise ValueError(tr('断面が中心軸に接触します。中心径を増やしてください。','The section reaches the axis. Increase the centerline diameter.'))
        circumference=2*math.pi*min_radius
        separation=result['pitch']*circumference/math.hypot(circumference,result['pitch'])
        if separation<=bound*2*1.01:
            raise ValueError(tr('巻き同士が接触します。ピッチを増やすか線径を小さくしてください。',
                                'Coil turns touch. Increase the pitch or reduce the wire diameter.'))
        number(result['pitch']*result['turns'],tr('コイルの高さ','Coil height'))
    if kind=='spiral':
        end_radius=planar_spiral.end_radius(result['diameter']/2,result['growth'],result['turns'])
        bound=result['section']/2 if result['section_kind']=='circular' else coil_sections.section_bound(result['section_kind'],result['section'])
        if bound>=result['diameter']/2 or result['growth']<=bound*2*1.05:
            raise ValueError(tr('断面が軸や隣の巻きに接触します。径や半径増分を増やしてください。','The section reaches the axis or adjacent turn. Increase diameter or radial growth.'))
    if kind=='pipe' and result['wall']*2>=result['diameter']:
        raise ValueError(tr('肉厚は外径の半分より小さくしてください。','Wall thickness must be less than half the outside diameter.'))
    return result


def check_solid(shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=1e-9:
        raise ValueError(tr('有効な立体を作成できません。寸法や経路の曲がり・自己交差を確認してください。',
                            'Cannot create a valid solid. Check dimensions, path bends and self-intersections.'))
    return shape


def swept_disk(spine,radius,frenet=False):
    edge=spine.OrderedEdges[0]
    # Respect reversed first edges (e.g. joined sketch geometry drawn backwards).
    parameter=edge.LastParameter if edge.Orientation=='Reversed' else edge.FirstParameter
    start=edge.valueAt(parameter);normal=edge.tangentAt(parameter)
    section=Part.Wire([Part.makeCircle(radius,start,normal)])
    return check_solid(spine.makePipeShell([section],True,frenet,1))


def shape(kind,**values):
    if kind=='dome':return check_solid(model_dome.shape(**values))
    p=validate(kind,values);radius=p['diameter']/2
    try:
        if kind=='sphere':result=Part.makeSphere(radius)
        elif kind=='torus':result=Part.makeTorus(radius,p['section']/2)
        elif kind=='coil':
            spine=coil_taper.spine(p['pitch'],p['turns'],radius,p['taper_angle'],p['left'])
            result=swept_disk(spine,p['section']/2,True) if p['section_kind']=='circular' else coil_sections.swept_polygon(spine,p['section_kind'],p['section'])
        elif kind=='spiral':
            spine=planar_spiral.spine(radius,p['growth'],p['turns'],p['left'])
            result=swept_disk(spine,p['section']/2,True) if p['section_kind']=='circular' else coil_sections.swept_polygon(spine,p['section_kind'],p['section'])
        elif p['section_kind']!='circular':
            spine=pipe_path_span.span(model_sections.wire(p['path'],False),p['path_fraction'],p['backward_fraction']) if p['path'] else Part.Wire([Part.makeLine(App.Vector(),App.Vector(0,0,p['length']))])
            rotation=p['path'].getGlobalPlacement().Rotation if p['path'] else App.Rotation()
            result=pipe_polygon.shape(p['section_kind'],p['diameter'],p['wall'],spine,rotation)
        elif p['path'] is None:
            outer=Part.makeCylinder(radius,p['length'])
            result=outer if p['wall']==0 else outer.cut(Part.makeCylinder(radius-p['wall'],p['length']))
        else:
            spine=pipe_path_span.span(model_sections.wire(p['path'],False),p['path_fraction'],p['backward_fraction'])
            outer=swept_disk(spine,radius)
            result=outer if p['wall']==0 else outer.cut(swept_disk(spine,radius-p['wall']))
        return check_solid(result)
    except (RuntimeError,Part.OCCError):
        raise ValueError(tr('この寸法・経路では作成できません。曲がりを緩くするか直径を小さくしてください。',
                            'Cannot build this geometry. Use gentler bends or a smaller diameter.')) from None


def placement(position=(0,0,0),axis='Z'):
    if axis not in ('X','Y','Z'):raise ValueError('Unknown axis')
    values=[number(v,tr('位置','Position'),-100000,100000) for v in position]
    if len(values)!=3:raise ValueError('Expected XYZ position')
    return App.Placement(App.Vector(*values),App.Rotation(App.Vector(0,0,1),
                         {'X':App.Vector(1,0,0),'Y':App.Vector(0,1,0),'Z':App.Vector(0,0,1)}[axis]))


def check_path(doc,path,existing=None):
    if path is None:return
    pipe_path_guard.checked(doc,path,existing)
    if path.Document!=doc:raise ValueError(tr('同じ文書内の経路を選んでください。','Select a path in the same document.'))
    if existing and (path==existing or existing in path.OutListRecursive):
        raise ValueError(tr('このパイプに依存する形状は経路に指定できません。','The path must not depend on this pipe.'))
    model_sections.wire(path,False)


class PrimitiveProxy:
    def __init__(self,obj):obj.Proxy=self

    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            values=settings(obj)
            if obj.FluxPrimitive=='pipe':
                if obj.UsePath and obj.FluxPath is None:
                    raise ValueError(tr('パイプの経路がありません。経路を選び直してください。','The pipe path is missing. Select a new path.'))
                values['path']=obj.FluxPath if obj.UsePath else None
                if values['path'] is not None:
                    pipe_path_guard.checked(obj.Document,values['path'],obj)
                    pipe_path_guard.verify_hierarchy(obj,values['path'])
            local=shape(obj.FluxPrimitive,**values)
            # Identity root keeps a moved feature's transform separate from its geometry.
            obj.Shape=Part.makeCompound([local]);obj.Placement=pose;obj.Error=''
        except Exception as error:
            obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)

    def dumps(self):return None
    def loads(self,state):pass


def create(doc,kind,existing=None,pose=None,**values):
    if kind=='pipe' and existing is not None and 'section_kind' not in values:values['section_kind']=settings(existing)['section_kind']
    if kind=='pipe' and existing is not None and 'path_fraction' not in values:values['path_fraction']=settings(existing)['path_fraction']
    if kind=='pipe' and existing is not None and 'backward_fraction' not in values:values['backward_fraction']=settings(existing)['backward_fraction']
    p=validate(kind,values)
    if existing and (existing.Document!=doc or getattr(existing,'FluxPrimitive',None)!=kind):
        raise ValueError(tr('同じ種類の形状を編集してください。','Edit a primitive of the same type.'))
    if kind=='pipe':check_path(doc,p['path'],existing)
    local=shape(kind,**p)
    pose=App.Placement(pose if pose is not None else existing.Placement if existing else App.Placement())
    if not all(math.isfinite(v) for v in tuple(pose.Base)+tuple(pose.Rotation.Q)):
        raise ValueError(tr('位置に有限の数値を指定してください。','Placement must contain finite numbers.'))
    import primitive_precision
    primitive_precision.check_placement(existing,pose)
    expected=local.copy();expected.Placement=pose.multiply(expected.Placement)
    solid_dependents={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    with model.transaction(doc,title(kind)):
        obj=existing
        if obj is None:
            obj=doc.addObject({'sphere':'Part::Sphere','torus':'Part::Torus'}.get(kind,'Part::FeaturePython'),kind.title())
            obj.Label=title(kind)
            obj.addProperty('App::PropertyString','FluxPrimitive','FluxCAD');obj.FluxPrimitive=kind;obj.setEditorMode('FluxPrimitive',2)
            if kind=='dome':
                model_dome.setup(obj);PrimitiveProxy(obj);obj.ViewObject.Proxy=0
            if kind in ('coil','spiral','pipe'):
                for typ,key in [('App::PropertyLength','Diameter')]+(
                    [('App::PropertyLength','Section'),('App::PropertyLength','Pitch' if kind=='coil' else 'Growth'),('App::PropertyFloat','Turns'),('App::PropertyBool','LeftHanded')]
                    if kind in ('coil','spiral') else [('App::PropertyLength','Wall'),('App::PropertyLength','Length'),('App::PropertyBool','UsePath'),('App::PropertyLinkGlobal','Path'),('App::PropertyLinkGlobal','FluxPath')]):
                    obj.addProperty(typ,key,'Dimensions')
                obj.addProperty('App::PropertyString','Error','FluxCAD');obj.setEditorMode('Error',1)
                if kind=='pipe':obj.setEditorMode('Path',2);obj.setEditorMode('FluxPath',2);obj.setEditorMode('UsePath',2)
                PrimitiveProxy(obj);obj.ViewObject.Proxy=0
        if kind=='sphere':obj.Radius=p['diameter']/2;obj.Angle1=-90;obj.Angle2=90;obj.Angle3=360
        elif kind=='torus':obj.Radius1=p['diameter']/2;obj.Radius2=p['section']/2;obj.Angle1=-180;obj.Angle2=180;obj.Angle3=360
        elif kind=='dome':model_dome.assign(obj,p)
        elif kind in ('coil','spiral'):
            if 'CoilSection' not in obj.PropertiesList:
                obj.addProperty('App::PropertyEnumeration','CoilSection','Dimensions')
                obj.CoilSection=['circular','square','triangle_out','triangle_in']
            if kind=='coil' and 'TaperAngle' not in obj.PropertiesList:
                obj.addProperty('App::PropertyAngle','TaperAngle','Dimensions')
            if kind=='coil':obj.TaperAngle=p['taper_angle']
            obj.CoilSection=p['section_kind']
            obj.Diameter=p['diameter'];obj.Section=p['section'];setattr(obj,'Pitch' if kind=='coil' else 'Growth',p['pitch'] if kind=='coil' else p['growth']);obj.Turns=p['turns'];obj.LeftHanded=p['left']
        else:
            if 'PipeSection' not in obj.PropertiesList:
                obj.addProperty('App::PropertyEnumeration','PipeSection','Dimensions');obj.PipeSection=['circular','square','triangle']
            obj.PipeSection=p['section_kind']
            if 'PathFraction' not in obj.PropertiesList:obj.addProperty('App::PropertyFloat','PathFraction','Dimensions')
            obj.PathFraction=p['path_fraction']
            if 'BackwardFraction' not in obj.PropertiesList:obj.addProperty('App::PropertyFloat','BackwardFraction','Dimensions')
            obj.BackwardFraction=p['backward_fraction']
            previous=obj.Path
            obj.Path=p['path']
            pipe_path_guard.assign(obj,p['path'])
            obj.FluxPath=p['path'];obj.UsePath=p['path'] is not None;obj.Diameter=p['diameter'];obj.Wall=p['wall'];obj.Length=p['length']
            if previous and previous!=obj.Path and getattr(previous,'FluxCADInternal',False) and not previous.InList:doc.removeObject(previous.Name)
        obj.Placement=pose;doc.recompute()
        check_solid(obj.Shape)
        if getattr(obj,'Error',''):raise ValueError(obj.Error)
        if abs(obj.Shape.Volume-expected.Volume)>max(1e-6,expected.Volume*1e-6):raise ValueError('Primitive preview/result mismatch')
        for dependent in obj.InListRecursive:
            if hasattr(dependent,'Shape') and (dependent.Shape.isNull() or not dependent.Shape.isValid() or 'Invalid' in dependent.State or getattr(dependent,'Error','')
                                               or (dependent.Name in solid_dependents and not dependent.Shape.Solids)):
                raise ValueError(tr('後続の加工が成立しないため変更を取り消しました。','The edit was cancelled because a later feature would become invalid.'))
        if not existing:
            obj.ViewObject.ShapeColor=(.72,.79,.85);obj.ViewObject.LineColor=(.18,.23,.29)
        if kind=='pipe' and p['path']:p['path'].Visibility=False;obj.Path.Visibility=False
    return obj
