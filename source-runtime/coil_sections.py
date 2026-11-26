import math

def section_points(kind, size):
    if not (isinstance(size, (int, float)) and math.isfinite(size) and size > 0):
        raise ValueError("size must be finite positive")
    pts = []
    if kind == "square":
        s = size / 2
        pts = [(-s, -s), (s, -s), (s, s), (-s, s)]
    elif kind == "triangle_out":
        r = size / math.sqrt(3)
        angles = [0, 2*math.pi/3, 4*math.pi/3]
        pts = [(r*math.cos(a), r*math.sin(a)) for a in angles]
    elif kind == "triangle_in":
        r = size / math.sqrt(3)
        angles = [math.pi, 5*math.pi/3, 7*math.pi/3]
        pts = [(r*math.cos(a), r*math.sin(a)) for a in angles]
    else:
        raise ValueError("Unknown kind")
    return pts

def section_bound(kind, size):
    pts = section_points(kind, size)
    return max(math.hypot(x, y) for x, y in pts)

def section_area(kind, size):
    pts = section_points(kind, size)
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area / 2.0)


def swept_polygon(spine, kind, size):
    import FreeCAD as App
    import Part
    edge=spine.OrderedEdges[0]
    t=edge.LastParameter if edge.Orientation=='Reversed' else edge.FirstParameter
    start=edge.valueAt(t);normal=edge.tangentAt(t);normal.normalize()
    radial=App.Vector(start.x,start.y,0)
    radial=radial-normal*radial.dot(normal);radial.normalize()
    binormal=normal.cross(radial);binormal.normalize()
    points=[start+radial*u+binormal*v for u,v in section_points(kind,size)]
    profile=Part.Wire(Part.makePolygon(points+[points[0]]).Edges)
    return spine.makePipeShell([profile],True,True,1)
