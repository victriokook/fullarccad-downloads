"""Independent editable native sketch curves from local font outlines."""
import math
import FreeCAD as App
import Part
from i18n import tr
import model
from text_sketch_values import checked,checked_count


def outline(text,font,height,tracking):
    text,height,tracking=checked(text,height,tracking)
    if type(font) is not str:raise ValueError(tr('フォントファイルを指定してください。','Specify a font file.'))
    from model_solid_text import validate
    values,font=validate(text,font,height,tracking,.1)
    groups=Part.makeWireString(text,font,height,tracking)
    wires=[w for group in groups for w in group]
    shape=Part.makeCompound(wires)
    checked_count(len(shape.Edges))
    bb=shape.BoundBox
    if any(not math.isfinite(x) or abs(x)>1e6 for x in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)):
        raise ValueError(tr('文字の座標が範囲外です。','Text coordinates are out of range.'))
    if not wires or any(not w.isClosed() for w in wires):raise ValueError(tr('文字輪郭が閉じていません。','Text outlines are not closed.'))
    faces=Part.makeFace(wires,'Part::FaceMakerBullseye')
    if faces.isNull() or not faces.isValid() or faces.Area<=1e-9:
        raise ValueError(tr('文字輪郭を有効な面にできません。','Text outlines cannot form valid faces.'))
    faces.check(True)
    return shape,faces


def create(doc,text,font,height=10,tracking=0):
    if App.ActiveDocument is not doc or doc is None:raise ValueError(tr('文書が変わりました。','The document changed.'))
    original,faces=outline(text,font,height,tracking)
    import Draft
    with model.transaction(doc,tr('文字をスケッチ曲線にする','Text as Sketch Curves')):
        out=Draft.make_sketch(original,autoconstraints=False,addTo=None,delete=False,name='TextSketch',tol=-1)
        doc.recompute()
        if (out is None or out.TypeId!='Sketcher::SketchObject' or out.GeometryCount!=len(original.Edges)
                or out.ConstraintCount or out.Shape.isNull() or not out.Shape.isValid()
                or out.OutList or any(s in out.State for s in ('Error','Invalid'))):
            raise ValueError(tr('文字をスケッチに変換できません。','Cannot convert text to a sketch.'))
        result=Part.makeFace(out.Shape.Wires,'Part::FaceMakerBullseye')
        tolerance=max(1e-7,faces.Area*1e-9)
        if (not result.isValid() or len(result.Faces)!=len(faces.Faces)
                or len(out.Shape.Wires)!=len(original.Wires)
                or faces.cut(result).Area+result.cut(faces).Area>tolerance):
            raise ValueError(tr('変換した文字輪郭が一致しません。','Converted text outlines do not match.'))
        for edge in original.Edges:
            for point in edge.discretize(Number=17):
                if Part.Vertex(point).distToShape(out.Shape)[0]>1e-7:
                    raise ValueError(tr('文字曲線の精度を確認できません。','Cannot verify text curve accuracy.'))
        out.Label=tr('文字スケッチ','Text Sketch')
    return out
