"""Forward prefix in native wire order; trimming uses native arc-length inversion."""
import math
import Part
from pipe_path_fraction_values import fraction

def prefix(wire,value):
    value=fraction(value)
    if value==1:return wire
    edges=wire.OrderedEdges
    length=wire.Length
    if not 1<=len(edges)<=200 or not math.isfinite(length) or not 1e-7<length<=1e7:
        raise ValueError('Partial pipe requires 1..200 edges and finite path length')
    target=length*value
    if target<=1e-7:raise ValueError('Partial path is too short')
    out=[];used=0
    for edge in edges:
        remain=target-used
        if remain<=0:break
        if remain>=edge.Length:
            out.append(edge.copy());used+=edge.Length
        else:
            # Reject numerically tiny terminal fragments instead of dropping them.
            if remain<=1e-7:raise ValueError('Partial endpoint is too close to an edge junction')
            reverse=edge.Orientation=='Reversed'
            parameter=edge.getParameterByLength(edge.Length-remain if reverse else remain)
            part=Part.Edge(edge.Curve,parameter,edge.LastParameter) if reverse else Part.Edge(edge.Curve,edge.FirstParameter,parameter)
            if reverse:part.reverse()
            out.append(part);used=target;break
    result=Part.Wire(out)
    if not result.isValid() or abs(result.Length-target)>max(1e-7,target*1e-10):
        raise ValueError('Partial path length mismatch')
    if any(not math.isfinite(v) or abs(v)>1e6 for vertex in result.Vertexes for v in tuple(vertex.Point)):
        raise ValueError('Partial path coordinates exceed limits')
    return result
