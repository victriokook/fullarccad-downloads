"""Shape-preserving one-degree native sketch B-spline elevation."""
import FreeCAD as App
import Part
import model
from conic_geometry import signature
from i18n import tr
from periodic_degree_limits import validate_periodic_curve


def checked(sketch,index):
    if not sketch or sketch.TypeId!='Sketcher::SketchObject' or sketch.Document is not App.ActiveDocument:
        raise ValueError(tr('現在のスケッチを指定してください。','Specify the current sketch.'))
    if type(index) is not int or not 0<=index<sketch.GeometryCount:raise ValueError('Invalid geometry index.')
    curve=sketch.Geometry[index]
    if not isinstance(curve,Part.BSplineCurve) or not 1<=curve.Degree<=8 or curve.NbPoles>200:
        raise ValueError(tr('次数1～8、制御点200以下のBスプラインを選択してください。','Select a B-spline of degree1–8 with at most200 poles.'))
    if curve.isPeriodic():validate_periodic_curve(curve.Degree,curve.NbPoles,curve.LastParameter-curve.FirstParameter)
    if any(index in (getattr(c,'First',-999),getattr(c,'Second',-999),getattr(c,'Third',-999)) for c in sketch.Constraints):
        raise ValueError(tr('選択スプラインの拘束や内部制御図形を先に解除してください。','Remove constraints and exposed internal control geometry from the selected spline first.'))
    if 'Invalid' in sketch.State or getattr(sketch,'Error',''):raise ValueError('Repair sketch errors first.')
    return curve


def elevate(sketch,index):
    before_curve=checked(sketch,index).copy();before=signature(sketch);doc=sketch.Document
    dependents={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in sketch.InListRecursive if hasattr(o,'Shape') and not o.Shape.isNull()}
    with model.transaction(doc,tr('スプラインの次数を上げる','Increase Spline Degree')):
        sketch.increaseBSplineDegree(index)
        if sketch.getConstruction(index)!=before[2][index]:sketch.setConstruction(index,before[2][index])
        doc.recompute()
        if sketch.solve()!=0:raise ValueError('The sketch could not be solved.')
        after=signature(sketch);curve=sketch.Geometry[index]
        if len(after[0])!=len(before[0]) or after[1:]!=before[1:] or any(a!=b for i,(a,b) in enumerate(zip(after[0],before[0])) if i!=index):
            raise ValueError('Other geometry or constraints changed; the operation was undone.')
        if curve.Degree!=before_curve.Degree+1 or curve.isPeriodic()!=before_curve.isPeriodic():raise ValueError('Native degree elevation failed.')
        if curve.NbPoles>1000:raise ValueError('Too many output poles.')
        a,b=before_curve.FirstParameter,before_curve.LastParameter
        if abs(curve.FirstParameter-a)>1e-12 or abs(curve.LastParameter-b)>1e-12:raise ValueError('Curve parameter range changed.')
        if max((before_curve.value(a+(b-a)*i/256.)-curve.value(a+(b-a)*i/256.)).Length for i in range(257))>1e-7:
            raise ValueError('Curve shape changed; the operation was undone.')
        if abs(before_curve.toShape().Length-curve.toShape().Length)>max(1e-7,before_curve.toShape().Length*1e-9):raise ValueError('Curve length changed.')
        for name,old in dependents.items():
            obj=doc.getObject(name);shape=getattr(obj,'Shape',None)
            if obj is None or 'Invalid' in obj.State or getattr(obj,'Error','') or shape is None or shape.isNull() or not shape.isValid() or any(was and not now for was,now in zip(old,(bool(shape.Solids),bool(shape.Faces),bool(shape.Edges)))):
                raise ValueError('A later feature became invalid; the operation was undone.')
    return curve.Degree
