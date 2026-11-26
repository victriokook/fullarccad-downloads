"""Analytic centers only; never substitute a shape centroid."""
import Part
from single_face_input import single_face
from center_point_values import center_coordinates


def point(shape):
    if shape.isNull() or not shape.isValid():raise ValueError("Choose valid circular or spherical/toroidal geometry")
    if shape.ShapeType=='Edge' and isinstance(shape.Curve,Part.Circle):
        center=shape.Curve.Center
    else:
        face=single_face(shape)
        if not isinstance(face.Surface,(Part.Sphere,Part.Toroid)):raise ValueError("Choose a circular edge or spherical/toroidal face")
        center=face.Surface.Center
    return Part.Vertex(*center_coordinates(tuple(center)))
