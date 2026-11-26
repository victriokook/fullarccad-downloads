"""Exact rational quadratic conics in sketch-local coordinates."""
import math
import FreeCAD as App
import Part
from conic_rho import conic_weight
from i18n import tr


def curve(start, end, vertex, rho):
    points = []
    for pair in (start, end, vertex):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError('Expected two sketch coordinates')
        values = []
        for value in pair:
            try:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError()
                value = float(value)
                if not math.isfinite(value) or abs(value) > 1e6:
                    raise ValueError()
            except (ValueError, OverflowError):
                raise ValueError(tr('座標は±1000000 mm以内の有限値にしてください。',
                                    'Coordinates must be finite and within ±1000000 mm.'))
            values.append(value)
        points.append(App.Vector(values[0], values[1], 0))
    a, b, v = points
    chord = b-a
    if min(chord.Length, (v-a).Length, (v-b).Length) <= 1e-6:
        raise ValueError(tr('3点を離して指定してください。', 'Specify three distinct points.'))
    if chord.cross(v-a).Length / chord.Length <= 1e-6:
        raise ValueError(tr('3点を一直線上に置くことはできません。',
                            'The three points must not be collinear.'))
    result = Part.BSplineCurve()
    result.buildFromPolesMultsKnots([a, v, b], [3, 3], [0., 1.], False, 2,
                                   [1., conic_weight(rho), 1.])
    return result


def signature(sketch):
    # Native geometry/constraint serialization also detects edits which retain counts.
    return (tuple(g.Content for g in sketch.Geometry),
            tuple(c.Content for c in sketch.Constraints),
            tuple(sketch.getConstruction(i) for i in range(sketch.GeometryCount)),
            str(sketch.getGlobalPlacement()))


def add(sketch, start, end, vertex, rho, construction=False):
    import model
    if getattr(sketch, 'TypeId', '') != 'Sketcher::SketchObject':
        raise ValueError(tr('スケッチを指定してください。', 'Specify a sketch.'))
    if not isinstance(construction, bool):
        raise ValueError('Construction must be boolean')
    geometry = curve(start, end, vertex, rho)
    doc = sketch.Document
    before = signature(sketch)
    count = sketch.GeometryCount
    dependents = [obj for obj in sketch.InListRecursive
                  if hasattr(obj, 'Shape') and not obj.Shape.isNull() and obj.Shape.isValid()]
    with model.transaction(doc, tr('円錐曲線を追加', 'Add Conic Curve')):
        index = sketch.addGeometry(geometry, construction)
        doc.recompute()
        if index != count or sketch.solve() != 0:
            raise ValueError(tr('スケッチを解けないため追加を取り消しました。',
                                'The sketch could not be solved; addition was undone.'))
        after = signature(sketch)
        if (after[0][:count] != before[0] or after[1] != before[1]
                or after[2][:count] != before[2] or after[3] != before[3]):
            raise ValueError(tr('既存の図形が変わったため追加を取り消しました。',
                                'Existing geometry changed; addition was undone.'))
        if any(obj.Shape.isNull() or not obj.Shape.isValid()
               or any(state in obj.State for state in ('Invalid', 'Error'))
               for obj in dependents):
            raise ValueError(tr('後の加工を更新できないため追加を取り消しました。',
                                'A dependent feature could not be updated; addition was undone.'))
    return index
