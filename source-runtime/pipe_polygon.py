import math
import FreeCAD as App
import Part
from pipe_polygon_values import inner_side

def profile(kind,size,origin,normal,rotation):
    normal.normalize()
    for axis in (App.Vector(1,0,0),App.Vector(0,1,0),App.Vector(0,0,1)):
        preferred=rotation.multVec(axis);u=preferred-normal*preferred.dot(normal)
        if u.Length>1e-7:u.normalize();break
    else:raise ValueError('Cannot define section frame')
    v=normal.cross(u)
    if kind=='square':points=[(-size/2,-size/2),(size/2,-size/2),(size/2,size/2),(-size/2,size/2)]
    else:points=[(size/math.sqrt(3)*math.cos(a),size/math.sqrt(3)*math.sin(a)) for a in (0,2*math.pi/3,4*math.pi/3)]
    points=[origin+u*x+v*y for x,y in points]
    return Part.Wire(Part.makePolygon(points+[points[0]]).Edges)

def shape(kind,size,wall,spine,rotation):
    inner=inner_side(kind,size,wall);edge=spine.OrderedEdges[0]
    parameter=edge.LastParameter if edge.Orientation=='Reversed' else edge.FirstParameter
    origin=edge.valueAt(parameter);normal=edge.tangentAt(parameter)
    outer=spine.makePipeShell([profile(kind,size,origin,normal,rotation)],True,False,1)
    if not wall:return outer
    return outer.cut(spine.makePipeShell([profile(kind,inner,origin,normal,rotation)],True,False,1))
