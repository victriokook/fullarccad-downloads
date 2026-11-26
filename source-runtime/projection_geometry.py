"""Directional projection of whole edge/wire onto one finite face.
All intersections (including front/back branches) are retained explicitly.
"""
import FreeCAD as App
import Part
from projection_direction import direction
from single_face_input import single_face


def projected(source, target, vector):
    axis = App.Vector(*direction(vector))
    if source.isNull() or not source.isValid() or source.ShapeType not in ("Edge", "Wire"):
        raise ValueError("Projection source must be one whole valid edge or wire")
    if not 1 <= len(source.Edges) <= 200 or source.Faces or source.Solids:
        raise ValueError("Projection source requires 1–200 edges")
    target = single_face(target)
    result = target.copy().makeParallelProjection(source.copy(), axis)
    if result.isNull() or not result.isValid() or result.Faces or result.Solids:
        raise ValueError("Projection did not create valid curves")
    edges = result.Edges
    if not 1 <= len(edges) <= 400 or any(e.Length <= 1e-9 for e in edges):
        raise ValueError("Projection produced no curves or too many curves")
    tolerance = max(1e-7, target.BoundBox.DiagonalLength * 1e-8)
    for edge in edges:
        for point in edge.discretize(Number=17):
            if Part.Vertex(point).distToShape(target)[0] > tolerance:
                raise ValueError("Projected curve leaves the finite target face")
    return result
