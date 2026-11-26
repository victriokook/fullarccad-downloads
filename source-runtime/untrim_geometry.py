"""Remove all internal wires of one finite face; preserve outer boundary."""
from single_face_input import single_face
from untrim_limits import internal_count


def filled(shape):
    face=single_face(shape);internal_count(len(face.Wires));out=face.copy()
    # Deliberately all holes, no area-threshold UI. Reject partial kernel results.
    if not out.removeInternalWires(1e100):raise ValueError("No internal holes could be removed")
    if out.isNull() or not out.isValid() or len(out.Faces)!=1 or out.Solids or len(out.Wires)!=1:raise ValueError("Not all internal boundaries were removed")
    result=out.Faces[0];tol=max(1e-7,face.Area*1e-7)
    if result.Area<=face.Area+tol or abs(face.common(result).Area-face.Area)>tol:raise ValueError("Original surface was lost or no holes were filled")
    outer=face.OuterWire;new=result.OuterWire
    if len(outer.Edges)!=len(new.Edges) or abs(outer.Length-new.Length)>max(1e-7,outer.Length*1e-7):raise ValueError("Outer boundary changed")
    unmatched=list(new.Edges)
    for edge in outer.Edges:
        matches=[i for i,candidate in enumerate(unmatched) if abs(edge.Length-candidate.Length)<=max(1e-7,edge.Length*1e-7) and abs(edge.common(candidate).Length-edge.Length)<=max(1e-7,edge.Length*1e-7) and edge.isSeam(face)==candidate.isSeam(result)]
        if len(matches)!=1:raise ValueError("Outer boundary edge mapping changed or is ambiguous")
        unmatched.pop(matches[0])
    if unmatched:raise ValueError("Outer boundary gained edges")
    for wire,other in ((outer,new),(new,outer)):
        for point in wire.discretize(Number=65):
            import Part
            if Part.Vertex(point).distToShape(other)[0]>1e-6:raise ValueError("Outer boundary moved")
    if face.Orientation!=result.Orientation:raise ValueError("Surface orientation changed")
    return result
