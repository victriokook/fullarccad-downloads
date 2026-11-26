import math
import FreeCAD as App
from FreeCAD import Vector
def checked(plane,position):
    if type(plane) is not str or plane not in ('XY','XZ','YZ') or type(position) not in (int,float):raise ValueError('Invalid section plane or position')
    try:position=float(position)
    except (ValueError,TypeError,OverflowError):raise ValueError('Invalid section position')
    if not math.isfinite(position) or abs(position)>1e6:raise ValueError('Section position out of bounds')
    return plane,position
def frame(plane, position):
    plane, pos = checked(plane, position)
    if plane == 'XY':
        base = Vector(0, 0, pos)
        rot = App.Rotation()
    elif plane == 'XZ':
        base = Vector(0, pos, 0)
        rot = App.Rotation(App.Vector(1, 0, 0), 90)
    elif plane == 'YZ':
        base = Vector(pos, 0, 0)
        rot = App.Rotation(App.Vector(0, 1, 0), 90)
    else:
        raise ValueError("Invalid plane")
    return App.Placement(base, rot)
def section_data(mesh, pose, plane, position, *, placement=None):
    plane, pos = checked(plane, position)
    sk_frame = frame(plane, pos) if placement is None else placement
    world_origin = sk_frame.Base
    world_normal = sk_frame.Rotation.multVec(Vector(0, 0, 1))
    inv_pose = pose.inverse()
    inv_rot = inv_pose.Rotation
    local_origin = inv_pose.multVec(world_origin)
    local_normal = inv_rot.multVec(world_normal)
    raw_sections = mesh.crossSections([(local_origin, local_normal)], 1e-7)
    if not raw_sections:
        raise ValueError("No section data returned")
    if len(raw_sections) != 1:
        raise ValueError("Expected exactly one plane section")
    polylines = raw_sections[0]
    if not polylines:
        raise ValueError("Empty section for plane")
    if sum(max(0,len(line)-1) for line in polylines)>20000:raise ValueError('Too many raw segments')
    all_points = []
    for polyline in polylines:
        for pt in polyline:
            all_points.append(pt)
    if not all_points:
        raise ValueError("No points in section")
    inv_sk_frame = sk_frame.inverse()
    transformed_points = []
    for pt in all_points:
        world_pt = pose.multVec(pt)
        sketch_pt = inv_sk_frame.multVec(world_pt)
        if any(not math.isfinite(c) or abs(c)>1e6 for c in world_pt):raise ValueError("World coordinates out of bounds")
        if not (math.isfinite(sketch_pt.x) and math.isfinite(sketch_pt.y) and math.isfinite(sketch_pt.z)):
            raise ValueError("Non-finite coordinates after transformation")
        if any(abs(c)>1e6 for c in sketch_pt):
            raise ValueError("Coordinates out of bounds")
        max_abs = max(abs(c) for c in world_pt)
        max_residual = max(1e-5, 2e-7 * max_abs)
        if abs(sketch_pt.z) > max_residual:
            raise ValueError("Point not coplanar with sketch plane")
        rx = round(sketch_pt.x, 6)
        ry = round(sketch_pt.y, 6)
        transformed_points.append((rx, ry))
    segments = []
    seen_segments = set()
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        for i in range(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i+1]
            w1 = pose.multVec(p1)
            s1 = inv_sk_frame.multVec(w1)
            rx1 = round(s1.x, 6)
            ry1 = round(s1.y, 6)
            w2 = pose.multVec(p2)
            s2 = inv_sk_frame.multVec(w2)
            rx2 = round(s2.x, 6)
            ry2 = round(s2.y, 6)
            if rx1 == rx2 and ry1 == ry2:
                continue
            pt1 = (rx1, ry1)
            pt2 = (rx2, ry2)
            seg_key = frozenset([pt1, pt2])
            if seg_key in seen_segments:
                continue
            seen_segments.add(seg_key)
            segments.append((Vector(rx1, ry1, 0), Vector(rx2, ry2, 0)))
    if len(segments) < 1 or len(segments) > 500:
        raise ValueError("Number of unique segments must be between 1 and 500")
    raw_segment_count = 0
    for polyline in polylines:
        if len(polyline) >= 2:
            raw_segment_count += len(polyline) - 1
    if raw_segment_count > 20000:
        raise ValueError("Too many raw segments")
    from collections import defaultdict
    adj = defaultdict(set)
    for start, end in segments:
        adj[tuple(start)].add(tuple(end))
        adj[tuple(end)].add(tuple(start))
    for node, neighbors in adj.items():
        if len(neighbors) > 2:
            raise ValueError("Graph degree exceeds 2")
    visited = set()
    components = 0
    for node in adj:
        if node not in visited:
            components += 1
            if components > 50:
                raise ValueError("Too many connected graph components")
            stack = [node]
            while stack:
                curr = stack.pop()
                if curr in visited:
                    continue
                visited.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        stack.append(neighbor)
    return (tuple(segments), sk_frame)
