"""Arc-length point on one edge or one connected wire."""
import Part
import math
from point_path_distance import distance_on_edge
from wire_point_segment import locate_segment
from wire_vertex_counts import validate_wire_vertices

def point(edge,mode,value,reverse=False):
    if edge.isNull() or not edge.isValid() or edge.Faces:
        raise ValueError("Choose one valid edge or wire")
    if edge.ShapeType=='Edge' and len(edge.Edges)==1:
        segment=edge
        distance=distance_on_edge(edge.Length,mode,value,reverse)
    elif edge.ShapeType=='Wire' and 1<=len(edge.Edges)<=200:
        ordered=edge.OrderedEdges
        if len(ordered)!=len(edge.Edges):raise ValueError("The wire must be a single connected path without repeated vertices")
        closed=edge.isClosed()
        validate_wire_vertices(len(ordered),len(edge.Vertexes),closed)
        following=ordered[1:]+([ordered[0]] if closed else [])
        for first,second in zip(ordered,following):
            a=first.valueAt(first.FirstParameter if first.Orientation=='Reversed' else first.LastParameter)
            b=second.valueAt(second.LastParameter if second.Orientation=='Reversed' else second.FirstParameter)
            if (a-b).Length>1e-7:raise ValueError("The wire must be connected without branches")
        lengths=[e.Length for e in ordered]
        index,distance=locate_segment(lengths,distance_on_edge(math.fsum(lengths),mode,value,reverse))
        segment=ordered[index]
    else:raise ValueError("Choose one whole edge or wire with at most 200 edges")
    if segment.Orientation=='Reversed':distance=segment.Length-distance
    parameter=segment.getParameterByLength(distance)
    return Part.Vertex(segment.valueAt(parameter))
