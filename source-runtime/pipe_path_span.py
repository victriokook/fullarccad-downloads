"""Closed-wire span anchored at its native seam; legacy forward path is exact."""
import math
import Part
from pipe_path_prefix import prefix
from pipe_two_sided_values import fractions

def endpoint(edge,start):
    reverse=edge.Orientation=='Reversed'
    return edge.valueAt(edge.LastParameter if start==reverse else edge.FirstParameter)

def span(wire,forward,backward):
    forward,backward=fractions(forward,backward,bool(wire.isClosed()))
    if backward==0:return prefix(wire,forward)
    edges=wire.OrderedEdges;length=wire.Length
    if not 1<=len(edges)<=200 or not math.isfinite(length) or not 1e-7<length<=1e7:
        raise ValueError('Two-sided pipe requires 1..200 edges and finite path length')
    if forward+backward==1:return wire
    seam=endpoint(edges[0],True)
    reverse_edges=[]
    for edge in reversed(edges):
        edge=edge.copy();edge.reverse();reverse_edges.append(edge)
    reverse=Part.Wire(reverse_edges)
    if (endpoint(reverse.OrderedEdges[0],True)-seam).Length>1e-7:
        raise ValueError('Reversed path changed its seam')
    back=prefix(reverse,backward);back.reverse()
    front=prefix(wire,forward)
    if (endpoint(back.OrderedEdges[-1],False)-seam).Length>1e-7:
        raise ValueError('Backward path does not join the native seam')
    result=Part.Wire(list(back.OrderedEdges)+list(front.OrderedEdges))
    target=length*(forward+backward)
    if not result.isValid() or result.isClosed() or abs(result.Length-target)>max(1e-7,target*1e-10):
        raise ValueError('Two-sided path length or connectivity mismatch')
    return result
