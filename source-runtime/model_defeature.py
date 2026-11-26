"""Editable face removal with healing; reject unchanged and partial results."""
import hashlib
import FreeCAD as App
import Part
import model
from i18n import tr
from defeature_faces import face_indices


def fingerprint(source):
    shape=source.Shape.copy();shape.Placement=App.Placement()
    return hashlib.sha256(shape.exportBrepToString().encode('utf-8')).hexdigest()


def solid(source):
    from model_combine import solid as checked
    shape=checked(source)
    if len(shape.Solids)!=1:
        raise ValueError(tr('単一のソリッドを選択してください。','Select a single solid.'))
    return shape


def containers(source):
    result=[];parent=source.getParentGeoFeatureGroup()
    while parent and parent not in result:
        result.append(parent);parent=parent.getParentGeoFeatureGroup()
    return result


def heal(shape,names):
    indices=face_indices(names,len(shape.Faces));faces=[shape.Faces[i] for i in indices]
    try:
        result=shape.defeaturing(faces).removeSplitter()
        if result.isNull() or not result.isValid() or len(result.Solids)!=1 or result.Volume<=1e-9:
            raise ValueError(tr('この面の組合せでは埋め直せません。','These faces cannot be healed.'))
        tolerance=max(1e-8,shape.Volume*1e-9)
        change=shape.cut(result).Volume+result.cut(shape).Volume
        if change<=tolerance:
            raise ValueError(tr('面を除去できませんでした。形状は変更されていません。','No faces were removed; the shape is unchanged.'))
        boundary=Part.makeCompound(result.Faces)
        if any(face.common(boundary).Area>max(1e-7,face.Area*1e-7) for face in faces):
            raise ValueError(tr('指定面の一部が残っています。除去する面を選び直してください。','Some selected faces remain. Reselect the feature faces.'))
        return result
    except (Part.OCCError,RuntimeError) as error:
        raise ValueError(tr('周囲の面で埋め直せません。面の組合せを変更してください。','Adjacent faces cannot heal this selection. Change the selected faces.')) from error


def check_reference(obj):
    if not obj.Source or obj.Source.Document!=obj.Document or fingerprint(obj.Source)!=obj.SourceFingerprint or containers(obj.Source)!=list(obj.SourceContainers):
        raise ValueError(tr('参照形状が変わりました。面を選び直してください。','The source geometry changed. Reselect faces.'))


class Defeature:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        pose=App.Placement(obj.Placement)
        try:
            check_reference(obj)
            result=heal(solid(obj.Source),list(obj.FaceNames))
            obj.Shape=Part.makeCompound([result]);obj.Placement=pose;obj.Error=''
        except Exception as error:
            obj.Shape=Part.Shape();obj.Placement=pose;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass


def preview(source,names,existing=None):
    result=heal(solid(source),names)
    if existing:result.Placement=existing.getGlobalPlacement().multiply(result.Placement)
    return result


def apply(doc,source,names,existing=None):
    names=list(names)
    if not source or source.Document!=doc or doc.getObject(source.Name)!=source:
        raise ValueError(tr('現在の文書のボディを選択してください。','Select a body in the current document.'))
    if existing and (existing.Document!=doc or not getattr(existing,'FluxDefeature',False) or existing.Source!=source or existing==source or existing in source.OutListRecursive):
        raise ValueError(tr('同じ参照元の面削除を編集してください。','Edit face removal with the same source.'))
    expected=preview(source,names,existing);stamp=fingerprint(source);parents=containers(source)
    if existing and list(existing.FaceNames)==names and existing.SourceFingerprint==stamp and list(existing.SourceContainers)==parents and not existing.Shape.isNull() and not existing.Error:return existing
    downstream={o.Name for o in existing.InListRecursive if hasattr(o,'Shape') and o.Shape.Solids} if existing else set()
    visible=bool(source.Visibility)
    try:
        with model.transaction(doc,tr('面を削除して埋める','Delete Faces and Heal')):
            obj=existing
            if obj is None:
                obj=doc.addObject('Part::FeaturePython','Defeature');obj.Label=tr('面削除・埋め直し','Delete Faces and Heal')
                for typ,name in [('App::PropertyBool','FluxDefeature'),('App::PropertyLinkGlobal','Source'),('App::PropertyLinkListGlobal','SourceContainers'),('App::PropertyStringList','FaceNames'),('App::PropertyString','SourceFingerprint'),('App::PropertyString','Error')]:obj.addProperty(typ,name,'FluxCAD')
                obj.FluxDefeature=True;obj.Source=source;obj.setEditorMode('FluxDefeature',2);obj.setEditorMode('Source',1)
                obj.setEditorMode('FaceNames',1);obj.setEditorMode('SourceFingerprint',2);obj.setEditorMode('Error',1)
                obj.setEditorMode('SourceContainers',2)
                Defeature(obj);obj.ViewObject.Proxy=0
                for name in ('ShapeColor','LineColor','PointColor','Transparency'):setattr(obj.ViewObject,name,getattr(source.ViewObject,name))
            obj.FaceNames=names;obj.SourceFingerprint=stamp;obj.SourceContainers=parents;doc.recompute();actual=model.world_shape(obj)
            tolerance=max(1e-6,expected.Volume*1e-7)
            if obj.Error or actual.isNull() or not actual.isValid() or 'Invalid' in obj.State or actual.cut(expected).Volume+expected.cut(actual).Volume>tolerance:
                raise ValueError(obj.Error or tr('プレビューと結果が一致しません。','Preview and result do not match.'))
            for child in obj.InListRecursive:
                if 'Invalid' in child.State or getattr(child,'Error','') or (hasattr(child,'Shape') and (child.Shape.isNull() or not child.Shape.isValid() or (child.Name in downstream and not child.Shape.Solids))):
                    raise ValueError(tr('後続の加工が成立しないため変更を取り消しました。','The edit was cancelled because a later feature would become invalid.'))
            if not existing:source.Visibility=False;obj.Visibility=True
        return obj
    except Exception:
        source.Visibility=visible
        raise
