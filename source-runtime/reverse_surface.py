"""Reviewed local-Qwen reverse proposal and native Part::Reverse adapter."""
import FreeCAD as App
import Part
import model
from i18n import tr

def reversed_surface(shape):
    if shape.isNull() or not shape.isValid() or shape.Solids or not shape.Faces:
        raise ValueError(tr('有効な面または殻を選択してください。','Select a valid face or shell.'))
    result=shape.copy();result.reverse()
    if result.isNull() or not result.isValid() or len(result.Faces)!=len(shape.Faces) or abs(result.Area-shape.Area)>max(1e-7,shape.Area*1e-9):
        raise ValueError(tr('法線を反転できません。','Cannot reverse the normals.'))
    return result

def preview(source):
    if source.Document!=App.ActiveDocument or source.Shape.ShapeType not in ('Face','Shell'):
        raise ValueError(tr('現在の文書の面・殻全体を選択してください。','Select a whole face or shell in the current document.'))
    if any('Invalid' in obj.State or getattr(obj,'Error','') for obj in [source]+source.OutListRecursive):
        raise ValueError(tr('参照元のエラーを修正してください。','Fix the source error first.'))
    return reversed_surface(model.world_shape(source))

def create(doc,source):
    expected=preview(source);visible=bool(source.Visibility)
    try:
        with model.transaction(doc,tr('法線を反転','Reverse Normal')):
            reference=model._world_source(doc,source)
            obj=doc.addObject('Part::Reverse','ReverseNormal');obj.Label=tr('法線反転','Reverse Normal')
            obj.Source=reference;obj.addProperty('App::PropertyBool','FluxSurfaceReverse','FluxCAD');obj.FluxSurfaceReverse=True;obj.setEditorMode('FluxSurfaceReverse',2)
            doc.recompute();actual=model.world_shape(obj)
            if actual.isNull() or not actual.isValid() or actual.Solids or len(actual.Faces)!=len(expected.Faces) or abs(actual.Area-expected.Area)>max(1e-7,expected.Area*1e-7) or actual.common(expected).Area<expected.Area-max(1e-7,expected.Area*1e-7):
                raise ValueError(tr('プレビューと結果が一致しません。','Preview and result do not match.'))
            for result,original in zip(actual.Faces,model.world_shape(source).Faces):
                u0,u1,v0,v1=original.ParameterRange;u=(u0+u1)/2;v=(v0+v1)/2
                if result.normalAt(u,v).dot(original.normalAt(u,v))>-.999999:raise ValueError(tr('面の向きが反転していません。','The face direction was not reversed.'))
            for name in ('ShapeColor','LineColor','Transparency'):setattr(obj.ViewObject,name,getattr(source.ViewObject,name))
            source.Visibility=False;reference.Visibility=False;obj.Visibility=True
        return obj
    except Exception:
        source.Visibility=visible;raise
