"""Explicit ASCII VertexN selection validation."""
import re

def vertex_name(value,count):
    if isinstance(count,bool) or not isinstance(count,int) or count<=0:
        raise ValueError('Invalid vertex count')
    if not isinstance(value,str) or not re.fullmatch(r'Vertex[1-9][0-9]*',value):
        raise ValueError('Select an explicit Vertex element')
    index=int(value[6:])-1
    if index>=count:raise ValueError('The selected vertex is missing')
    return index
