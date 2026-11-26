"""Native one-degree approximation with sampled deviation acceptance."""
import FreeCAD as App
import Part
import model
from conic_geometry import signature
from i18n import tr
from spline_reduction_values import validate_tolerance


def checked(sketch,index):
    if not sketch or sketch.TypeId!='Sketcher::SketchObject' or sketch.Document is not App.ActiveDocument:
        raise ValueError(tr('現在のスケッチを指定してください。','Specify the current sketch.'))
    if type(index) is not int or not 0<=index<sketch.GeometryCount:raise ValueError('Invalid geometry index.')
    curve=sketch.Geometry[index]
    if not isinstance(curve,Part.BSplineCurve) or curve.isPeriodic() or not 2<=curve.Degree<=9 or curve.NbPoles>50:
        raise ValueError(tr('次数2～9、制御点50以下の非周期Bスプラインを選択してください。','Select a nonperiodic B-spline of degree2–9 with at most50 poles.'))
    if any(index in (getattr(c,'First',-999),getattr(c,'Second',-999),getattr(c,'Third',-999)) for c in sketch.Constraints):
        raise ValueError(tr('選択スプラインの拘束や内部制御図形を先に解除してください。','Remove constraints and exposed internal control geometry from the selected spline first.'))
    if 'Invalid' in sketch.State or getattr(sketch,'Error',''):raise ValueError('Repair sketch errors first.')
    return curve


def reduce(sketch,index,tolerance=.1):
    tolerance=validate_tolerance(tolerance)
    before_curve=checked(sketch,index).copy();before=signature(sketch);doc=sketch.Document
    dependents={o.Name:(bool(o.Shape.Solids),bool(o.Shape.Faces),bool(o.Shape.Edges)) for o in sketch.InListRecursive if hasattr(o,'Shape') and not o.Shape.isNull()}
    # Native reduction deletes/re-appends the selected curve and exposes internal geometry.
    # Obtain only its approximation inside an aborted transaction, then replace the original slot.
    doc.openTransaction('Native degree reduction probe')
    try:
        old_count=sketch.GeometryCount
        if not sketch.decreaseBSplineDegree(index):raise ValueError('Native degree reduction failed.')
        doc.recompute()
        approximation=sketch.Geometry[old_count-1].copy()
        if not isinstance(approximation,Part.BSplineCurve) or approximation.Degree!=before_curve.Degree-1:raise ValueError('Native approximation not found.')
    finally:
        doc.abortTransaction();doc.recompute()
    if signature(sketch)!=before:raise ValueError('Native preview restoration failed.')
    with model.transaction(doc,tr('スプラインの次数を下げる','Decrease Spline Degree')):
        geometries=list(sketch.Geometry);geometries[index]=approximation;sketch.Geometry=geometries
        if sketch.getConstruction(index)!=before[2][index]:sketch.setConstruction(index,before[2][index])
        doc.recompute()
        if sketch.solve()!=0:raise ValueError('The sketch could not be solved.')
        after=signature(sketch);curve=sketch.Geometry[index]
        if len(after[0])!=len(before[0]) or after[1:]!=before[1:] or any(a!=b for i,(a,b) in enumerate(zip(after[0],before[0])) if i!=index):
            raise ValueError('Other geometry or constraints changed; the operation was undone.')
        if curve.Degree!=before_curve.Degree-1 or curve.isPeriodic()!=before_curve.isPeriodic():raise ValueError('Native degree reduction failed.')
        a,b=before_curve.FirstParameter,before_curve.LastParameter
        if abs(curve.FirstParameter-a)>1e-12 or abs(curve.LastParameter-b)>1e-12:raise ValueError('Curve parameter range changed.')
        if curve.NbPoles>1000 or not curve.toShape().isValid():raise ValueError('Native approximation is invalid or too large.')
        # Sampling measures parameter-corresponding displacement; it is not a global Hausdorff bound.
        fractions={i/1024. for i in range(1025)}
        knots=sorted(set([0.,1.]+[(k-a)/(b-a) for k in before_curve.getKnots()+curve.getKnots() if a<=k<=b]))
        fractions.update(knots);fractions.update((x+y)/2 for x,y in zip(knots,knots[1:]))
        error=max((before_curve.value(a+(b-a)*t)-curve.value(a+(b-a)*t)).Length for t in fractions)
        if error>tolerance:raise ValueError(tr('測定点の変位 %.9g mm が上限 %.9g mm を超えたため取り消しました。','Sampled displacement %.9g mm exceeds limit %.9g mm; the edit was undone.')%(error,tolerance))
        for name,old in dependents.items():
            obj=doc.getObject(name);shape=getattr(obj,'Shape',None)
            if obj is None or 'Invalid' in obj.State or getattr(obj,'Error','') or shape is None or shape.isNull() or not shape.isValid() or any(was and not now for was,now in zip(old,(bool(shape.Solids),bool(shape.Faces),bool(shape.Edges)))):
                raise ValueError('A later feature became invalid; the operation was undone.')
    return curve.Degree,error,curve.NbPoles
