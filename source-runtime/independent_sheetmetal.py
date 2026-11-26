"""Independent rectangular, chained-bend sheet prototype, authored 2026-11-02.

Geometry is constructed analytically with FreeCAD Part. No SheetMetal addon
imports or copied addon algorithms. Lengths are straight tangent lengths.
Flat bend allowance = angle_in_radians * (inside_radius + K * thickness).
"""
import math
import json
import FreeCAD as App
import Part

SCHEMA = 14  # Older readers cannot reconstruct curved cutouts.
ROOT_KINDS = ('Base','PerforatedBase')
MAX_HOLES = 32
MAX_BENDS = 8
BASE_EDGES = ('+X','-X','+Y','-Y')

def number(v, name, lo, hi):
    v=float(v)
    if not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError('%s must be between %g and %g' % (name,lo,hi))
    return v

def dimensions(length,width,thickness):
    length=number(length,'Length',1,10000)
    width=number(width,'Width',1,10000)
    thickness=number(thickness,'Thickness',.05,100)
    if thickness > min(length,width)/4:
        raise ValueError('Thickness must not exceed one quarter of either plate dimension')
    return length,width,thickness

def bend_values(radius,angle,height,k):
    angle=number(angle,'Signed bend angle',-180,180)
    if abs(angle)<1:raise ValueError('Absolute bend angle must be at least 1 degree')
    return (number(radius,'Inside radius',.05,10000),angle,
            number(height,'Flange straight length',1,10000),number(k,'K factor',0,1))

def valid(shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:
        raise ValueError('The result must be one valid positive-volume solid')
    return shape

def base_shape(length,width,thickness):
    return valid(Part.makeBox(*dimensions(length,width,thickness)))

def cutout_clearance_shape(hole):
    if hole.get('rect_width'):
        return hole['rect_width']/2, hole['rect_height']/2, 0
    hx, hy = hole_axis(hole)
    return hx, hy, hole['radius']


def rectangle_corners(hole):
    hx, hy, _ = cutout_clearance_shape(hole)
    x, y = hole['x'], hole['y']
    return [(x-hx,y-hy),(x+hx,y-hy),(x+hx,y+hy),(x-hx,y+hy)]


def polygon_corners(hole):
    return [(hole['x']+dx, hole['y']+dy) for dx, dy in hole['polygon']]


def polygon_face(hole, z=0):
    points = [App.Vector(x, y, z) for x, y in polygon_corners(hole)]
    if any((a-b).Length < .05 for a, b in zip(points, points[1:]+points[:1])):
        raise ValueError('Polygon sides must be at least 0.05 mm long')
    wire = Part.makePolygon(points+[points[0]])
    face = Part.Face(wire)
    if not face.isValid() or face.Area <= 1e-7:
        raise ValueError('Polygon must enclose a simple, nonintersecting area')
    return face


def hole_axis(hole):
    half = hole.get('span', 0) / 2
    return (0, half) if hole.get('vertical', False) else (half, 0)


def profile_face(hole, z=0):
    edges = []
    for segment in hole['profile']:
        points = [App.Vector(hole['x']+x, hole['y']+y, z) for x, y in segment]
        edge = Part.makeLine(*points) if len(points) == 2 else Part.Arc(*points).toShape()
        if edge.Length < .05:
            raise ValueError('Outline edges must be at least 0.05 mm long')
        edges.append(edge)
    groups = Part.sortEdges(edges)
    if len(groups) != 1:
        raise ValueError('The sketch must contain one closed outline')
    wire = Part.Wire(groups[0])
    if not wire.isClosed() or not wire.isValid():
        raise ValueError('The sketch must contain one closed outline')
    face = Part.Face(wire)
    if not face.isValid() or face.Area <= 1e-7:
        raise ValueError('The outline must enclose a simple area')
    return face


def cutouts_from_sketch(base, sketch, *, deflection=.005):
    """Copy closed sketch loops into base-local coordinates."""
    owned(base, 'Base')
    if sketch.Document != base.Document or not sketch.isDerivedFrom('Sketcher::SketchObject'):
        raise ValueError('Select a sketch in the same document')
    sketch.Document.recompute()
    if not sketch.isValid():
        raise ValueError('The sketch must recompute successfully')
    length, width, thickness = source_dimensions(base)
    transform = base.getGlobalPlacement().inverse().multiply(sketch.getGlobalPlacement())
    normal = transform.Rotation.multVec(App.Vector(0,0,1))
    if math.hypot(normal.x, normal.y) > 1e-8:
        raise ValueError('The sketch must be parallel to the base')
    deflection = number(deflection, 'Curve subdivision setting (mm)', .001, .05)
    edges = []
    cutouts = []
    for index, curve in enumerate(sketch.Geometry):
        if sketch.getConstruction(index):
            continue
        if isinstance(curve, Part.Circle):
            center = transform.multVec(curve.Center)
            cutouts.append(dict(x=center.x, y=center.y, radius=curve.Radius))
            continue
        if isinstance(curve, Part.LineSegment):
            samples = (curve.StartPoint, curve.EndPoint)
        elif isinstance(curve, Part.ArcOfCircle):
            first, last = curve.FirstParameter, curve.LastParameter
            samples = [curve.value(t) for t in (first, (first+last)/2, last)]
        elif isinstance(curve, (Part.Ellipse, Part.ArcOfEllipse, Part.BSplineCurve)):
            samples = curve.toShape().discretize(Deflection=deflection)
        else:
            raise ValueError('Use lines, circles, circular arcs, ellipses or B-splines')
        points = [transform.multVec(point) for point in samples]
        points = [App.Vector(point.x, point.y, 0) for point in points]
        if isinstance(curve, Part.ArcOfCircle):
            new_edges = [Part.Arc(*points).toShape()]
        else:
            new_edges = [Part.makeLine(a,b) for a,b in zip(points, points[1:])]
        if any(edge.Length < .05 for edge in new_edges):
            raise ValueError('Outline edges must be at least 0.05 mm long')
        edges.extend(new_edges)
    for group in Part.sortEdges(edges) if edges else []:
        if not 2 <= len(group) <= 512:
            raise ValueError('Each sketch outline must have 2 to 512 edges')
        wire = Part.Wire(group)
        if not wire.isClosed() or not wire.isValid():
            raise ValueError('Each sketch outline must be closed')
        if all(isinstance(edge.Curve, Part.Line) for edge in group):
            points = [vertex.Point for vertex in wire.OrderedVertexes]
            x = sum(point.x for point in points)/len(points)
            y = sum(point.y for point in points)/len(points)
            cutouts.append(dict(x=x, y=y, radius=.05,
                                polygon=[(point.x-x, point.y-y) for point in points]))
            continue
        origin = group[0].valueAt(group[0].FirstParameter)
        profile = []
        for edge in group:
            first, last = edge.FirstParameter, edge.LastParameter
            parameters = (first, last) if isinstance(edge.Curve, Part.Line) else (first, (first+last)/2, last)
            points = [edge.valueAt(t)-origin for t in parameters]
            profile.append([(point.x, point.y) for point in points])
        cutouts.append(dict(x=origin.x, y=origin.y, radius=.05, profile=profile))
    if not cutouts:
        raise ValueError('The sketch must contain at least one closed outline')
    return hole_values(length, width, thickness, cutouts)


def polygon_from_sketch(base, sketch):
    cutouts = cutouts_from_sketch(base, sketch)
    if len(cutouts) != 1:
        raise ValueError('Select a sketch containing one closed outline')
    return cutouts[0]


def hole_values(length, width, thickness, holes):
    if not isinstance(holes, (list, tuple)) or len(holes) > MAX_HOLES:
        raise ValueError('Specify at most 32 cutouts')
    result = []
    for index, hole in enumerate(holes, 1):
        x = number(hole['x'], 'Hole X', 0, length)
        y = number(hole['y'], 'Hole Y', 0, width)
        radius = number(hole['radius'], 'Hole radius', .05, min(length, width) / 2)
        span = number(hole.get('span', 0), 'Slot straight length', 0, max(length, width))
        vertical = hole.get('vertical', False)
        if not isinstance(vertical, bool) or 0 < span < .05:
            raise ValueError('Choose X or Y and a straight length of zero or at least 0.05 mm')
        cutout = dict(x=x, y=y, radius=radius, span=span, vertical=vertical)
        rw = number(hole.get('rect_width', 0), 'Opening width', 0, length)
        rh = number(hole.get('rect_height', 0), 'Opening height', 0, width)
        if (rw or rh) and min(rw, rh) < .05:
            raise ValueError('Enter both rectangle dimensions, at least 0.05 mm')
        cutout.update(rect_width=rw, rect_height=rh)
        if hole.get('profile'):
            segments = hole['profile']
            if not isinstance(segments, (list, tuple)) or not 2 <= len(segments) <= 512:
                raise ValueError('The outline must have 2 to 512 edges')
            if rw or rh or span or hole.get('polygon'):
                raise ValueError('Clear other outline dimensions before using a curved profile')
            cutout['profile'] = []
            for segment in segments:
                if len(segment) not in (2, 3):
                    raise ValueError('Use two points for a line or three for a circular arc')
                cutout['profile'].append([
                    (number(dx, 'Profile X offset', -length, length),
                     number(dy, 'Profile Y offset', -width, width))
                    for dx, dy in segment
                ])
            cutter = hole_tool(cutout, thickness)
            box = cutter.BoundBox
            if min(box.XMin, length-box.XMax, box.YMin, width-box.YMax) < thickness-1e-7:
                raise ValueError('Cutout must leave at least one thickness to the plate edge')
            if not cutter.isValid():
                raise ValueError('Invalid curved cutout')
            if any(cutter.distToShape(hole_tool(old, thickness))[0] < thickness-1e-7 for old in result):
                raise ValueError('Cutouts must leave at least one thickness between boundaries')
            result.append(cutout)
            continue
        vertices = hole.get('polygon', [])
        if vertices:
            if not isinstance(vertices, (tuple, list)) or not 3 <= len(vertices) <= 512:
                raise ValueError('Polygon must have 3 to 512 vertices')
            if rw or rh or span:
                raise ValueError('Set rectangle dimensions and slot length to zero for a polygon')
            cutout['polygon'] = [
                (number(dx, 'Vertex X offset', -length, length),
                 number(dy, 'Vertex Y offset', -width, width))
                for dx, dy in vertices
            ]
            for px, py in polygon_corners(cutout):
                if min(px, length-px, py, width-py) < thickness-1e-7:
                    raise ValueError('Polygon must leave at least one thickness to the plate edge')
            cutter = hole_tool(cutout, thickness)
            if not cutter.isValid():
                raise ValueError('Invalid polygon cutout')
            if any(cutter.distToShape(hole_tool(old, thickness))[0] < thickness-1e-7 for old in result):
                raise ValueError('Cutouts must leave at least one thickness between boundaries')
            result.append(cutout)
            continue
        hx, hy, radius = cutout_clearance_shape(cutout)
        if min(x-hx, length-x-hx, y-hy, width-y-hy) < radius+thickness-1e-7:
            raise ValueError('Cutout %d must leave at least one thickness to the plate edge' % index)
        for old in result:
            if old.get('polygon') or old.get('profile'):
                if hole_tool(cutout, thickness).distToShape(hole_tool(old, thickness))[0] < thickness-1e-7:
                    raise ValueError('Cutouts must leave at least one thickness between boundaries')
                continue
            ox, oy, old_radius = cutout_clearance_shape(old)
            # The axes are horizontal/vertical segments, including points for circles.
            dx = max(0, abs(x-old['x'])-hx-ox)
            dy = max(0, abs(y-old['y'])-hy-oy)
            if math.hypot(dx, dy) < radius+old_radius+thickness-1e-7:
                raise ValueError('Cutouts must leave at least one thickness between boundaries')
        result.append(cutout)
    return result


def slot_profile(hole, z=0):
    hx, hy = hole_axis(hole)
    r = hole['radius']
    axis = App.Vector(hx, hy, 0)
    direction = axis / axis.Length
    normal = App.Vector(-direction.y, direction.x, 0)
    center = App.Vector(hole['x'], hole['y'], z)
    start, end = center-axis, center+axis
    return start, end, direction, normal, r


def hole_tool(hole, thickness):
    if hole.get('profile'):
        return profile_face(hole, -thickness).extrude(App.Vector(0, 0, 3*thickness))
    if hole.get('polygon'):
        return polygon_face(hole, -thickness).extrude(App.Vector(0, 0, 3*thickness))
    if hole.get('rect_width'):
        x, y = rectangle_corners(hole)[0]
        return Part.makeBox(hole['rect_width'], hole['rect_height'], 3*thickness, App.Vector(x,y,-thickness))
    if not hole.get('span', 0):
        return Part.makeCylinder(hole['radius'], 3*thickness, App.Vector(hole['x'], hole['y'], -thickness))
    start, end, direction, normal, radius = slot_profile(hole, -thickness)
    a, b = start-normal*radius, end-normal*radius
    c, d = end+normal*radius, start+normal*radius
    wire = Part.Wire([
        Part.makeLine(a, b), Part.Arc(b, end+direction*radius, c).toShape(),
        Part.makeLine(c, d), Part.Arc(d, start-direction*radius, a).toShape(),
    ])
    return Part.Face(wire).extrude(App.Vector(0, 0, 3*thickness))


def cut_holes(shape, holes, thickness):
    if not holes:
        return valid(shape)
    tools = [hole_tool(hole, thickness) for hole in holes]
    expected = shape.Volume - sum(tool.Volume for tool in tools)/3
    result = valid(shape.cut(Part.makeCompound(tools)).removeSplitter())
    if abs(result.Volume-expected) > max(1e-6, shape.Volume*1e-8):
        raise ValueError('Unexpected removed cutout volume')
    return result


def perforated_shape(length,width,thickness,holes):
    holes=hole_values(length,width,thickness,holes)
    return cut_holes(base_shape(length,width,thickness),holes,thickness)

def decode_holes(obj):
    text=obj.HoleSpec
    if len(text)>131072:raise ValueError('Hole data is too large')
    return json.loads(text)

def panel_root(obj):
    obj=owned(obj)
    if obj.IndependentSheetKind=='Flat':obj=owned(obj.Source)
    if obj.IndependentSheetKind=='Tray':return owned(obj.Source)
    return chain(obj)[0]

def holes_of(source):
    base=panel_root(source)
    if base.IndependentSheetKind=='PerforatedBase':return hole_values(*source_dimensions(base),decode_holes(base))
    return []

def flat_holes(source):
    base=panel_root(source);holes=holes_of(base)
    if source.IndependentSheetKind=='Tray':return holes
    inverse=root_frame(*source_dimensions(base)[:2],edge_of(source)).inverse()
    result=[]
    for hole in holes:
        point=inverse.multVec(App.Vector(hole['x'],hole['y'],0))
        axis = inverse.Rotation.multVec(App.Vector(0,1,0) if hole['vertical'] else App.Vector(1,0,0))
        transformed = dict(hole, x=point.x, y=point.y, vertical=abs(axis.y)>.5)
        if abs(inverse.Rotation.multVec(App.Vector(1,0,0)).y) > .5:
            transformed['rect_width'], transformed['rect_height'] = hole['rect_height'], hole['rect_width']
        if hole.get('polygon'):
            offsets = [inverse.Rotation.multVec(App.Vector(dx,dy,0)) for dx,dy in hole['polygon']]
            transformed['polygon'] = [(v.x,v.y) for v in offsets]
        if hole.get('profile'):
            transformed['profile'] = []
            for segment in hole['profile']:
                offsets = [inverse.Rotation.multVec(App.Vector(dx,dy,0)) for dx,dy in segment]
                transformed['profile'].append([(v.x,v.y) for v in offsets])
        result.append(transformed)
    return result

def bend_segment(width,thickness,radius,angle,height):
    """Local XZ annular sector + straight flange, starting at the last tangent."""
    radius,angle,height,_=bend_values(radius,angle,height,.5)
    a=math.radians(abs(angle));positive=angle>0;outer=radius+thickness
    def point(rad,theta):
        return App.Vector(rad*math.sin(theta),0,
                          outer-rad*math.cos(theta) if positive else -radius+rad*math.cos(theta))
    os,oe=point(outer,0),point(outer,a)
    ins,ine=point(radius,0),point(radius,a)
    direction=App.Vector(math.cos(a),0,math.sin(a) if positive else -math.sin(a))*height
    edges=[Part.Arc(os,point(outer,a/2),oe).toShape(),Part.makeLine(oe,oe+direction),
           Part.makeLine(oe+direction,ine+direction),Part.makeLine(ine+direction,ine),
           Part.Arc(ine,point(radius,a/2),ins).toShape(),Part.makeLine(ins,os)]
    shape=valid(Part.Face(Part.Wire(edges)).extrude(App.Vector(0,width,0)))
    return shape,(oe if positive else ine)+direction

def root_frame(length,width,edge):
    if edge not in BASE_EDGES:raise ValueError('Choose +X, -X, +Y or -Y on the rectangular base')
    position,angle={'+X':((0,0,0),0),'-X':((length,width,0),180),
                    '+Y':((length,0,0),90),'-Y':((0,width,0),-90)}[edge]
    return App.Placement(App.Vector(*position),App.Rotation(App.Vector(0,0,1),angle))

def edge_from_selection(base,name):
    base=owned(base)
    if base.IndependentSheetKind not in ROOT_KINDS:raise ValueError('Select an independent base panel')
    if not name.startswith('Edge') or not name[4:].isdigit():raise ValueError('Select a complete horizontal boundary edge')
    edge=base.getSubObject(name)
    if edge is None or edge.ShapeType!='Edge' or len(edge.Vertexes)!=2:raise ValueError('Select a complete boundary edge')
    inverse=base.Placement.inverse();points=[inverse.multVec(v.Point) for v in edge.Vertexes]
    length,width,t=source_dimensions(base);tol=1e-6
    close=lambda a,b:abs(a-b)<tol
    if not any(all(close(p.z,z) for p in points) for z in (0,t)):
        raise ValueError('Thickness edges cannot start a flange')
    for label,x in (('+X',length),('-X',0)):
        if all(close(p.x,x) for p in points) and close(min(p.y for p in points),0) and close(max(p.y for p in points),width):return label
    for label,y in (('+Y',width),('-Y',0)):
        if all(close(p.y,y) for p in points) and close(min(p.x for p in points),0) and close(max(p.x for p in points),length):return label
    raise ValueError('Select a full-width edge of the independent rectangular base')

def chain_shape(length,width,thickness,bends,edge='+X',holes=None,*,start=None):
    length,width,thickness=dimensions(length,width,thickness)
    if len(bends)>MAX_BENDS:raise ValueError('At most %d sequential bends are supported'%MAX_BENDS)
    frame=root_frame(length,width,edge)
    tangent_length,strip_width=(width,length) if edge in ('+Y','-Y') else (length,width)
    flange_cutters=[]
    if start is None:
        result=perforated_shape(length,width,thickness,holes or [])
    else:
        tangent_length=start
        result=Part.makeBox(start,strip_width,thickness)
        result.Placement=frame
        radius,angle,_,k=bends[0]
        end_tangent=start+allowance(radius,angle,thickness,k)
        inverse=frame.inverse()
        for hole in holes or []:
            cutter=hole_tool(hole,thickness)
            local_placement=inverse.multiply(cutter.Placement)
            cutter.Placement=local_placement
            bounds=cutter.BoundBox
            if bounds.XMax<start-1e-6:
                cutter.Placement=frame.multiply(local_placement)
                result=valid(result.cut(cutter).removeSplitter())
            elif bounds.XMin>end_tangent+1e-6:
                flange_cutters.append(cutter)
            else:
                raise ValueError('An opening touches or crosses the bend zone')
    pieces=[result]
    origin=frame.multVec(App.Vector(tangent_length,0,0));turn=0
    for index,(radius,angle,height,k) in enumerate(bends):
        radius,angle,height,k=bend_values(radius,angle,height,k)
        segment,end=bend_segment(strip_width,thickness,radius,angle,height)
        rotation=frame.Rotation.multiply(App.Rotation(App.Vector(0,1,0),-turn))
        segment.Placement=App.Placement(origin,rotation)
        if index==0 and flange_cutters:
            fold=App.Rotation(App.Vector(0,1,0),-angle)
            direction=fold.multVec(App.Vector(1,0,0))
            local_origin=end-direction*(height+end_tangent)
            local_fold=App.Placement(local_origin,fold)
            placement=segment.Placement.multiply(local_fold)
            for cutter in flange_cutters:
                cutter.Placement=placement.multiply(cutter.Placement)
                segment=valid(segment.cut(cutter).removeSplitter())
        # Non-neighbouring sheet sections must remain separate, including touching.
        if any(segment.distToShape(prior)[0]<1e-6 for prior in pieces[:-1]):
            raise ValueError('Bend intersects or touches an earlier sheet section')
        expected=result.Volume+segment.Volume
        joined=valid(result.fuse(segment).removeSplitter())
        if abs(joined.Volume-expected)>max(1e-6,expected*1e-8):
            raise ValueError('Bend overlaps the existing sheet')
        result=joined;pieces.append(segment)
        origin=origin+rotation.multVec(end);turn+=angle
    return valid(result)

def bent_shape(length,width,thickness,radius,angle,height):
    return chain_shape(length,width,thickness,[(radius,angle,height,.5)])

WALL_PREFIX={'+X':'PositiveX','-X':'NegativeX','+Y':'PositiveY','-Y':'NegativeY'}

def default_walls():
    return [dict(edge=edge,enabled=True,radius=2,angle=90,height=20,k=.4) for edge in BASE_EDGES]

def tray_values(length,width,thickness,gap,walls):
    length,width,thickness=dimensions(length,width,thickness)
    gap=number(gap,'Wall end setback',thickness,min(length,width)/2-thickness)
    if len(walls)!=4 or {v['edge'] for v in walls}!=set(BASE_EDGES):
        raise ValueError('Specify each of the four tray sides exactly once')
    by_edge={v['edge']:v for v in walls};normalized=[]
    for edge in BASE_EDGES:
        v=by_edge[edge]
        if type(v['enabled']) is not bool:raise ValueError('Wall enabled must be a boolean')
        radius,angle,height,k=bend_values(v['radius'],v['angle'],v['height'],v['k'])
        span = length if edge in ('+Y','-Y') else width
        setback = number(v.get('setback',0) or gap,'Wall start setback',thickness,span-thickness)
        end_setback = number(v.get('end_setback',0) or setback,'Wall end setback',thickness,span-thickness)
        if span-setback-end_setback < 2*thickness:
            raise ValueError('Wall setbacks must leave at least two thicknesses of wall width')
        normalized.append(dict(edge=edge,enabled=v['enabled'],radius=radius,angle=angle,height=height,k=k,setback=setback,end_setback=end_setback))
    if not any(v['enabled'] for v in normalized):raise ValueError('Enable at least one wall')
    return gap,normalized

def relieved_tray_base(length,width,thickness,walls,holes,size):
    base=perforated_shape(length,width,thickness,holes or [])
    size=number(size,'Relief size',0,min(length,width)/2)
    if not size:
        return base
    for wall in walls:
        if not wall['enabled']:
            continue
        edge=wall['edge']
        if size>min(wall['setback'],wall['end_setback']):
            raise ValueError(f'Relief exceeds the end setbacks on {edge}')
        frame=root_frame(length,width,edge)
        tangent,span=(width,length) if edge in ('+Y','-Y') else (length,width)
        for y in (wall['setback']-size,span-wall['end_setback']):
            cutter=Part.makeBox(size,size,thickness)
            cutter.Placement=App.Placement(frame.multVec(App.Vector(tangent-size,y,0)),frame.Rotation)
            expected=base.Volume-size*size*thickness
            base=valid(base.cut(cutter).removeSplitter())
            if abs(base.Volume-expected)>max(1e-7,size*size*thickness*1e-8):
                raise ValueError(f'Relief on {edge} overlaps an opening or another relief')
    return base


def tray_shape(length,width,thickness,gap,walls,holes=None,*,clearances=None,relief=0):
    gap,walls=tray_values(length,width,thickness,gap,walls)
    result=relieved_tray_base(length,width,thickness,walls,holes,relief);pieces=[]
    for v in walls:
        if not v['enabled']:continue
        gap=v['setback']
        edge=v['edge'];frame=root_frame(length,width,edge)
        tangent,span=(width,length) if edge in ('+Y','-Y') else (length,width)
        piece,_=bend_segment(span-gap-v['end_setback'],thickness,v['radius'],v['angle'],v['height'])
        piece.Placement=App.Placement(frame.multVec(App.Vector(tangent,gap,0)),frame.Rotation)
        for prior_edge,prior_piece in pieces:
            distance = piece.distToShape(prior_piece)[0]
            if distance < 1e-6:
                raise ValueError(f'Tray walls {prior_edge} and {edge} intersect or touch')
            if clearances is not None:
                clearances.append((distance,prior_edge,edge))
        expected=result.Volume+piece.Volume;joined=valid(result.fuse(piece).removeSplitter())
        if abs(joined.Volume-expected)>max(1e-6,expected*1e-8):raise ValueError('Wall overlaps the sheet')
        result=joined;pieces.append((edge,piece))
    return valid(result)

def tray_development(source):
    source=owned(source,'Tray');length,width,t=source_dimensions(source.Source)
    gap,walls=tray_values(length,width,t,source.CornerGap.Value,settings(source)['walls'])
    result=relieved_tray_base(length,width,t,walls,holes_of(source.Source),settings(source)['relief'])
    for v in walls:
        if not v['enabled']:continue
        gap=v['setback']
        edge=v['edge'];depth=allowance(v['radius'],v['angle'],t,v['k'])+v['height']
        frame=root_frame(length,width,edge)
        tangent,span=(width,length) if edge in ('+Y','-Y') else (length,width)
        wing=Part.makeBox(depth,span-gap-v['end_setback'],t)
        wing.Placement=App.Placement(frame.multVec(App.Vector(tangent,gap,0)),frame.Rotation)
        expected=result.Volume+wing.Volume
        result=valid(result.fuse(wing).removeSplitter())
        if abs(result.Volume-expected)>max(1e-6,expected*1e-8):raise ValueError('Developed wings overlap')
    return result

def tray_summary(source):
    _,_,t=source_dimensions(source.Source);walls=settings(source)['walls']
    return sum(v['enabled'] for v in walls),sum(allowance(v['radius'],v['angle'],t,v['k']) for v in walls if v['enabled'])

def allowance(radius,angle,thickness,k):
    radius,angle,_,k=bend_values(radius,angle,1,k)
    thickness=number(thickness,'Thickness',.05,100)
    return math.radians(abs(angle))*(radius+k*thickness)

def owned(obj,kind=None):
    if obj is None or obj.Document is None or obj.Document.getObject(obj.Name)!=obj:
        raise ValueError('Select a current document object')
    if getattr(obj,'IndependentSheetSchema',0) not in (1,2,3,4,5,6,7,8,9,10,11,12,13,SCHEMA) or not isinstance(getattr(obj,'Proxy',None),Feature):
        raise ValueError('Select a plate created by the independent sheet prototype')
    if kind is not None and obj.IndependentSheetKind!=kind:
        raise ValueError('Select an independent '+kind+' object')
    if obj.getParentGeoFeatureGroup() is not None:
        raise ValueError('This prototype supports root-level objects only')
    if obj.Error or obj.Shape.isNull() or not obj.Shape.isValid():
        raise ValueError('Repair the source parameters first')
    return obj

def settings(obj):
    kind=obj.IndependentSheetKind
    if kind=='Base':return dict(length=obj.Length.Value,width=obj.Width.Value,thickness=obj.Thickness.Value)
    if kind=='PerforatedBase':return dict(holes=decode_holes(obj))
    if kind=='Bend':
        values=dict(radius=obj.InsideRadius.Value,angle=obj.BendAngle,height=obj.FlangeLength.Value,k=obj.KFactor)
        if obj.Source.IndependentSheetKind in ROOT_KINDS:values['edge']=str(getattr(obj,'BaseEdge','+X'))
        if hasattr(obj,'BendCenter'):values['center']=obj.BendCenter.Value
        return values
    if kind=='Tray':
        walls=[]
        for edge,prefix in WALL_PREFIX.items():
            walls.append(dict(edge=edge,enabled=bool(getattr(obj,prefix+'Enabled')),radius=getattr(obj,prefix+'Radius').Value,angle=getattr(obj,prefix+'Angle'),height=getattr(obj,prefix+'Length').Value,k=getattr(obj,prefix+'KFactor'),setback=getattr(obj,prefix+'Setback',0).Value if hasattr(obj,prefix+'Setback') else 0,end_setback=getattr(obj,prefix+'EndSetback').Value if hasattr(obj,prefix+'EndSetback') else 0))
        return dict(gap=obj.CornerGap.Value,walls=walls,relief=obj.ReliefSize.Value if hasattr(obj,'ReliefSize') else 0)
    return {}

def bend_line_from_sketch(base, sketch):
    owned(base)
    if base.IndependentSheetKind not in ROOT_KINDS:
        raise ValueError('Select a base plate')
    if sketch.Document!=base.Document or not sketch.isDerivedFrom('Sketcher::SketchObject'):
        raise ValueError('Select a sketch in the same document')
    sketch.Document.recompute()
    lines=[curve for index,curve in enumerate(sketch.Geometry) if not sketch.getConstruction(index)]
    if not sketch.isValid() or len(lines)!=1 or not isinstance(lines[0],Part.LineSegment):
        raise ValueError('Use a sketch containing one straight line')
    transform=base.getGlobalPlacement().inverse().multiply(sketch.getGlobalPlacement())
    a,b=[transform.multVec(point) for point in (lines[0].StartPoint,lines[0].EndPoint)]
    if abs(a.z-b.z)>1e-6:
        raise ValueError('The bend line must be parallel to the plate')
    length,width,_=source_dimensions(base)
    if abs(a.x-b.x)<1e-6 and abs(a.y-b.y)>1e-6 and min(a.y,b.y)<=1e-6 and max(a.y,b.y)>=width-1e-6:
        return '+X',(a.x+b.x)/2
    if abs(a.y-b.y)<1e-6 and abs(a.x-b.x)>1e-6 and min(a.x,b.x)<=1e-6 and max(a.x,b.x)>=length-1e-6:
        return '+Y',(a.y+b.y)/2
    raise ValueError('The bend line must cross the full plate parallel to an edge')


def positioned_bend(source, values):
    if 'center' not in values:
        return None,bend_values(values['radius'],values['angle'],values['height'],values['k'])
    owned(source)
    if source.IndependentSheetKind not in ROOT_KINDS:
        raise ValueError('A positioned bend must start on a base plate')
    length,width,thickness=source_dimensions(source)
    span=width if values.get('edge','+X') in ('+Y','-Y') else length
    center=number(values['center'],'Bend center',0,span)
    ba=allowance(values['radius'],values['angle'],thickness,values['k'])
    start=center-ba/2
    if start<1:
        raise ValueError('Leave at least 1 mm of flat material before the bend')
    return start,bend_values(values['radius'],values['angle'],span-center-ba/2,values['k'])


def chain_start(source):
    if source.IndependentSheetKind!='Bend':
        return None
    while source.Source.IndependentSheetKind=='Bend':
        source=source.Source
    return positioned_bend(source.Source,settings(source))[0]


def chain(source):
    """Read only our parametric graph; never infer bends from imported geometry."""
    doc=source.Document if source is not None else None
    bends=[];seen=set();current=source
    while True:
        current=owned(current)
        if current.Document!=doc or current.Name in seen:raise ValueError('Invalid or cyclic sheet source chain')
        seen.add(current.Name)
        if current.IndependentSheetKind in ROOT_KINDS:
            root=owned(current.Source,'Base') if current.IndependentSheetKind=='PerforatedBase' else current
            dimensions(root.Length.Value,root.Width.Value,root.Thickness.Value)
            return current,list(reversed(bends))
        if current.IndependentSheetKind!='Bend':raise ValueError('Select an independent Base or Bend')
        bends.append(positioned_bend(current.Source,settings(current))[1])
        if len(bends)>MAX_BENDS:raise ValueError('Too many bends in source chain')
        current=current.Source

def edge_of(source):
    _,bends=chain(source)
    if not bends:return '+X'
    current=source
    while current.Source.IndependentSheetKind not in ROOT_KINDS:current=current.Source
    edge=str(getattr(current,'BaseEdge','+X'))
    if edge not in BASE_EDGES:raise ValueError('Invalid base edge')
    return edge

def source_dimensions(obj):
    base,_=chain(obj)
    if base.IndependentSheetKind=='PerforatedBase':base=owned(base.Source,'Base')
    return dimensions(base.Length.Value,base.Width.Value,base.Thickness.Value)

def development(source):
    base,bends=chain(source)
    length,width,t=source_dimensions(base)
    if edge_of(source) in ('+Y','-Y'):length,width=width,length
    start=chain_start(source)
    if start is not None:length=start
    markers=[];total_ba=0
    for radius,angle,height,k in bends:
        ba=allowance(radius,angle,t,k);markers.append((length,ba,angle))
        length+=ba+height;total_ba+=ba
    return length,width,t,markers,total_ba

def geometry(kind,source,values):
    if kind=='Base':return base_shape(**values)
    if kind=='PerforatedBase':
        source=owned(source,'Base')
        return perforated_shape(*source_dimensions(source),values['holes'])
    if kind=='Tray':
        source=owned(source)
        if source.IndependentSheetKind not in ROOT_KINDS:raise ValueError('Select a base panel for the tray')
        return tray_shape(*source_dimensions(source),values['gap'],values['walls'],holes=holes_of(source),relief=values.get('relief',0))
    if kind=='Bend':
        base,bends=chain(source)
        start,bend=positioned_bend(source,values)
        bends.append(bend)
        if start is None:start=chain_start(source)
        edge=values.get('edge','+X') if source.IndependentSheetKind in ROOT_KINDS else edge_of(source)
        if source.IndependentSheetKind=='Bend' and 'edge' in values and values['edge']!=edge:
            raise ValueError('Choose the base edge on the first bend, not on a child flange')
        return chain_shape(*source_dimensions(base),bends,edge=edge,holes=holes_of(base),start=start)
    if kind=='Flat':
        source=owned(source)
        if source.IndependentSheetKind=='Tray':return tray_development(source)
        source=owned(source,'Bend');length,width,t,_,_=development(source)
        return cut_holes(Part.makeBox(length,width,t),flat_holes(source),t)
    raise ValueError('Unknown independent sheet feature')

class Feature:
    def execute(self,obj):
        try:
            kind=obj.IndependentSheetKind
            shape=geometry(kind,getattr(obj,'Source',None),settings(obj))
            placement=obj.Placement
            if kind!='Base':
                if kind=='PerforatedBase':owned(obj.Source,'Base')
                elif kind=='Tray':
                    owned(obj.Source)
                    if obj.Source.IndependentSheetKind not in ROOT_KINDS:raise ValueError('Select a base panel')
                elif kind=='Flat' and obj.Source.IndependentSheetKind=='Tray':owned(obj.Source,'Tray')
                else:chain(obj.Source)
                placement=obj.Source.Placement
            obj.Shape=shape
            obj.Placement=placement
            if kind=='PerforatedBase':
                obj.Length,obj.Width,obj.Thickness=source_dimensions(obj.Source)
                obj.HoleCount=len(settings(obj)['holes']);obj.BendCount=0;obj.BendAllowance=0
            elif kind=='Bend':
                if hasattr(obj,'BendCenter'):
                    obj.FlangeLength=positioned_bend(obj.Source,settings(obj))[1][2]
                obj.BendAllowance=allowance(obj.InsideRadius.Value,obj.BendAngle,source_dimensions(obj.Source)[2],obj.KFactor)
            elif kind=='Tray':
                obj.BendCount,obj.BendAllowance=tray_summary(obj)
            elif kind=='Flat':
                obj.DevelopedLength=shape.BoundBox.XLength
                if hasattr(obj,'DevelopedWidth'):obj.DevelopedWidth=shape.BoundBox.YLength
                if obj.Source.IndependentSheetKind=='Tray':obj.BendCount,obj.BendAllowance=tray_summary(obj.Source)
                else:obj.BendAllowance=development(obj.Source)[4]
            if hasattr(obj,'BendCount') and kind=='Bend':obj.BendCount=len(chain(obj.Source)[1])+1
            elif hasattr(obj,'BendCount') and kind=='Flat' and obj.Source.IndependentSheetKind=='Bend':obj.BendCount=len(chain(obj.Source)[1])
            obj.Error=''
        except Exception as exc:
            obj.Shape=Part.Shape();obj.Error=str(exc)
            raise RuntimeError('Independent sheet: '+str(exc))
    def dumps(self):return None
    def loads(self,state):pass

class ViewProvider:
    def __init__(self,vobj):vobj.Proxy=self
    def getDisplayModes(self,vobj):return []
    def getDefaultDisplayMode(self):return 'Flat Lines'
    def attach(self,vobj):pass
    def updateData(self,obj,prop):pass
    def onChanged(self,vobj,prop):pass
    def doubleClicked(self,vobj):
        import FreeCADGui as Gui
        import independent_sheetmetal_ui
        ws=getattr(Gui,'fluxcad_workspace',None)
        if ws is not None and vobj.Object.IndependentSheetKind!='Flat':
            ws.safe(lambda:independent_sheetmetal_ui.show(ws,vobj.Object.IndependentSheetKind,existing=vobj.Object))
            return True
        return False
    def dumps(self):return None
    def loads(self,state):pass

def assign(obj,values):
    mapping={'length':'Length','width':'Width','thickness':'Thickness','radius':'InsideRadius','angle':'BendAngle','height':'FlangeLength','k':'KFactor','edge':'BaseEdge','gap':'CornerGap','center':'BendCenter','relief':'ReliefSize'}
    for key,value in values.items():
        if key=='holes':obj.HoleSpec=json.dumps(value,separators=(',',':'),allow_nan=False)
        elif key=='walls':
            for wall in value:
                prefix=WALL_PREFIX[wall['edge']]
                for field,suffix in (('setback','Setback'),('end_setback','EndSetback')):
                    name=prefix+suffix
                    if not hasattr(obj,name):
                        obj.addProperty('App::PropertyLength',name,'Wall '+wall['edge'])
                    setattr(obj,name,wall.get(field,0))
                for field,suffix in [('enabled','Enabled'),('radius','Radius'),('angle','Angle'),('height','Length'),('k','KFactor')]:setattr(obj,prefix+suffix,wall[field])
        else:setattr(obj,mapping[key],value)

def make(doc,kind,source=None,existing=None,*,_transaction=True,**values):
    if doc is None or App.ActiveDocument!=doc:raise ValueError('Use the active document')
    if source is not None and source.Document!=doc:raise ValueError('Source must belong to the active document')
    if existing is not None:
        owned(existing,kind)
        if existing.Document!=doc:raise ValueError('Wrong document')
        if kind!='Base' and source!=existing.Source:raise ValueError('Reparenting a sheet feature is not supported')
        if existing.ExpressionEngine:raise ValueError('Edit expressions in the property editor')
        values={**settings(existing),**values}
    geometry(kind,source,values)  # Validate before creating or modifying any object.
    if kind=='PerforatedBase':values['holes']=hole_values(*source_dimensions(source),values['holes'])
    targets=[]
    if kind=='PerforatedBase' and existing is None:
        targets=[child for child in source.InList if isinstance(getattr(child,'Proxy',None),Feature) and child.IndependentSheetKind in ('Bend','Tray') and child.Source==source]
        if any(child.ExpressionEngine for target in targets for child in [target,*target.InListRecursive]):
            raise ValueError('Automatic hole linking does not support expressions; use a separate plain base')
    if _transaction:doc.openTransaction('Independent sheet '+kind)
    try:
        obj=existing
        if obj is None:
            obj=doc.addObject('Part::FeaturePython','IndependentSheet'+kind)
            obj.addProperty('App::PropertyInteger','IndependentSheetSchema','Independent Sheet');obj.IndependentSheetSchema=SCHEMA;obj.setEditorMode('IndependentSheetSchema',1)
            obj.addProperty('App::PropertyString','IndependentSheetKind','Independent Sheet');obj.IndependentSheetKind=kind;obj.setEditorMode('IndependentSheetKind',1)
            obj.addProperty('App::PropertyString','Error','Independent Sheet');obj.setEditorMode('Error',1)
            if kind=='Base':
                for name in ('Length','Width','Thickness'):obj.addProperty('App::PropertyLength',name,'Independent Sheet')
            else:
                obj.addProperty('App::PropertyLink','Source','Independent Sheet');obj.Source=source;obj.setEditorMode('Source',1)
                obj.addProperty('App::PropertyInteger','BendCount','Independent Sheet');obj.setEditorMode('BendCount',1)
                obj.addProperty('App::PropertyLength','BendAllowance','Independent Sheet');obj.setEditorMode('BendAllowance',1)
                if kind=='Bend':
                    for name in ('InsideRadius','FlangeLength'):obj.addProperty('App::PropertyLength',name,'Independent Sheet')
                    obj.addProperty('App::PropertyFloat','BendAngle','Independent Sheet')
                    obj.addProperty('App::PropertyFloat','KFactor','Independent Sheet')
                elif kind=='PerforatedBase':
                    obj.addProperty('App::PropertyString','HoleSpec','Independent Sheet');obj.setEditorMode('HoleSpec',1)
                    obj.addProperty('App::PropertyInteger','HoleCount','Independent Sheet');obj.setEditorMode('HoleCount',1)
                    for name in ('Length','Width','Thickness'):
                        obj.addProperty('App::PropertyLength',name,'Independent Sheet');obj.setEditorMode(name,1)
                elif kind=='Tray':
                    obj.addProperty('App::PropertyLength','CornerGap','Independent Sheet')
                    for edge,prefix in WALL_PREFIX.items():
                        for suffix,prop_type in [('Enabled','Bool'),('Radius','Length'),('Angle','Float'),('Length','Length'),('KFactor','Float')]:
                            obj.addProperty('App::Property'+prop_type,prefix+suffix,'Wall '+edge)
                else:
                    for name in ('DevelopedLength','DevelopedWidth'):
                        obj.addProperty('App::PropertyLength',name,'Independent Sheet');obj.setEditorMode(name,1)
            obj.Proxy=Feature()
            if App.GuiUp:
                ViewProvider(obj.ViewObject);obj.ViewObject.ShapeColor=(.72,.79,.86)
        if kind=='Bend' and source.IndependentSheetKind in ROOT_KINDS:
            # Old readers otherwise ignore BaseEdge and silently rebuild along +X.
            source.IndependentSheetSchema=SCHEMA;obj.IndependentSheetSchema=SCHEMA
            if not hasattr(obj,'BaseEdge'):
                obj.addProperty('App::PropertyEnumeration','BaseEdge','Independent Sheet');obj.BaseEdge=list(BASE_EDGES)
        if kind=='Tray':
            source.IndependentSheetSchema=SCHEMA
            for dependent in source.InListRecursive:
                if isinstance(getattr(dependent,'Proxy',None),Feature):dependent.IndependentSheetSchema=SCHEMA
        if kind == 'PerforatedBase' and any(hole['span'] or hole['rect_width'] or hole.get('polygon') or hole.get('profile') for hole in values['holes']):
            # Preview 5 validates the source schema before reconstructing the cutouts.
            source.IndependentSheetSchema = SCHEMA
            obj.IndependentSheetSchema = SCHEMA
            for dependent in obj.InListRecursive:
                if isinstance(getattr(dependent, 'Proxy', None), Feature):
                    dependent.IndependentSheetSchema = SCHEMA
        if kind=='Bend' and 'center' in values and not hasattr(obj,'BendCenter'):
            obj.addProperty('App::PropertyLength','BendCenter','Independent Sheet')
            obj.setEditorMode('FlangeLength',1)
        if kind=='Tray' and 'relief' in values and not hasattr(obj,'ReliefSize'):
            obj.addProperty('App::PropertyLength','ReliefSize','Independent Sheet')
        assign(obj,values);obj.Proxy.execute(obj)
        for target in targets:
            target.Source=obj
            for child in [target,*target.InListRecursive]:
                if isinstance(getattr(child,'Proxy',None),Feature):child.IndependentSheetSchema=SCHEMA
        doc.recompute()
        if obj.Error or obj.Shape.isNull():raise ValueError(obj.Error or 'Empty result')
        for dependent in obj.InListRecursive:
            if isinstance(getattr(dependent,'Proxy',None),Feature) and (dependent.Error or dependent.Shape.isNull()):
                raise ValueError('Edit would invalidate a downstream sheet feature: '+dependent.Name)
        if source is not None and App.GuiUp:
            source.Visibility=False
            if targets and any(child.Visibility for child in obj.InListRecursive if isinstance(getattr(child,'Proxy',None),Feature)):
                obj.Visibility=False
        if _transaction:doc.commitTransaction()
        return obj
    except Exception:
        if _transaction:
            doc.abortTransaction()
            doc.recompute()
        raise

def make_jog(doc,source,*,radius,angle,height,k,return_length,edge=None):
    if abs(angle)>=90:
        raise ValueError('A jog angle must be smaller than 90 degrees')
    if doc is None or App.ActiveDocument!=doc or source.Document!=doc:
        raise ValueError('Use a source in the active document')
    base,bends = chain(source)
    first_bend = bend_values(radius,angle,height,k)
    second_bend = bend_values(radius,-angle,return_length,k)
    bend_edge = (edge or '+X') if source.IndependentSheetKind in ROOT_KINDS else edge_of(source)
    chain_shape(*source_dimensions(base),bends+[first_bend,second_bend],
                edge=bend_edge,holes=holes_of(base),start=chain_start(source))
    first = dict(radius=radius,angle=angle,height=height,k=k)
    if edge is not None:
        first['edge'] = edge
    doc.openTransaction('Independent sheet jog')
    try:
        step = make(doc,'Bend',source=source,_transaction=False,**first)
        result = make(doc,'Bend',source=step,_transaction=False,
                      radius=radius,angle=-angle,height=return_length,k=k)
        doc.commitTransaction()
        return result
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise

def bend_rows(source):
    source=owned(source)
    if source.IndependentSheetKind=='Flat':source=owned(source.Source)
    rows=[]
    if source.IndependentSheetKind=='Tray':
        length,width,t=source_dimensions(source.Source)
        _,walls=tray_values(length,width,t,source.CornerGap.Value,settings(source)['walls'])
        for v in walls:
            if not v['enabled']:continue
            gap=v['setback']
            edge=v['edge'];frame=root_frame(length,width,edge)
            tangent,span=(width,length) if edge in ('+Y','-Y') else (length,width)
            ba=allowance(v['radius'],v['angle'],t,v['k'])
            p=frame.multVec(App.Vector(tangent+ba/2,gap,0));q=frame.multVec(App.Vector(tangent+ba/2,span-v['end_setback'],0))
            rows.append(dict(v,sequence=len(rows)+1,width=span-gap-v['end_setback'],allowance=ba,center=(p.x,p.y,q.x,q.y),tangents=[tuple(frame.multVec(App.Vector(x,y,0)))[:2] for x in (tangent,tangent+ba) for y in (gap,span-v['end_setback'])]))
    elif source.IndependentSheetKind=='Bend':
        base,bends=chain(source);_,width,t,markers,_=development(source)
        for index,((r,a,h,k),(position,ba,_)) in enumerate(zip(bends,markers),1):
            rows.append(dict(sequence=index,edge=edge_of(source),radius=r,angle=a,height=h,k=k,width=width,allowance=ba,center=(position+ba/2,0,position+ba/2,width),tangents=[(position,0),(position,width),(position+ba,0),(position+ba,width)]))
    else:raise ValueError('Select an independent Bend, Tray or Flat for a bend table')
    return rows

def flat_top_face(flat):
    flat = owned(flat, 'Flat')
    source = flat.Source
    shape = geometry('Flat', source, {})
    thickness = source_dimensions(panel_root(source))[2]
    faces = [
        face for face in shape.Faces
        if abs(face.BoundBox.ZMin-thickness) < 1e-6
        and abs(face.BoundBox.ZMax-thickness) < 1e-6
        and face.normalAt(0, 0).z > .99
    ]
    if len(faces) != 1 or len(faces[0].Wires) != 1+len(flat_holes(source)):
        raise ValueError('Developed outline/hole topology does not match the hole data')
    return faces[0]


def make_flat_sketch(flat):
    flat = owned(flat, 'Flat')
    doc = flat.Document
    doc.recompute()
    face = flat_top_face(flat)

    def xy(point):
        return App.Vector(point.x, point.y, 0)

    profiles = []
    for wire in face.Wires:
        for edge in wire.Edges:
            curve = edge.Curve
            if isinstance(curve, Part.Line):
                a, b = (xy(vertex.Point) for vertex in edge.Vertexes)
                profiles.append(Part.LineSegment(a, b))
            elif isinstance(curve, Part.Circle):
                first, last = edge.FirstParameter, edge.LastParameter
                if abs(last-first-2*math.pi) < 1e-7:
                    profiles.append(Part.Circle(xy(curve.Center), App.Vector(0, 0, 1), curve.Radius))
                else:
                    points = [xy(edge.valueAt(t)) for t in (first, (first+last)/2, last)]
                    profiles.append(Part.Arc(*points))
            else:
                raise ValueError('Unsupported curve in developed profile')
    centers = [
        Part.LineSegment(App.Vector(x1, y1, 0), App.Vector(x2, y2, 0))
        for x1, y1, x2, y2 in (row['center'] for row in bend_rows(flat.Source))
    ]
    doc.openTransaction('Developed sheet sketch')
    try:
        sketch = doc.addObject('Sketcher::SketchObject', 'IndependentFlatSketch')
        sketch.Label = flat.Label + ' - XY sketch'
        sketch.addGeometry(profiles, False)
        if centers:
            sketch.addGeometry(centers, True)
        doc.recompute()
        if sketch.GeometryCount != len(profiles)+len(centers) or sketch.Shape.isNull():
            raise ValueError('Could not create the developed sketch')
        doc.commitTransaction()
        return sketch
    except Exception:
        doc.abortTransaction()
        raise


def refresh_flats(doc):
    flats = [
        obj for obj in doc.Objects
        if isinstance(getattr(obj, 'Proxy', None), Feature)
        and obj.IndependentSheetKind == 'Flat'
    ]
    for flat in flats:
        flat.touch()
    doc.recompute()
    errors = [flat.Label for flat in flats if flat.Error or flat.Shape.isNull()]
    return len(flats)-len(errors), errors


def export_dxf(flat,path,*,closed_polylines=False,include_bends=True):
    flat = owned(flat, 'Flat')
    flat.Document.recompute()
    face = flat_top_face(flat)
    circles = flat_holes(flat.Source)
    pairs=[(0,'SECTION'),(2,'HEADER'),(9,'$ACADVER'),(1,'AC1015'),(9,'$INSUNITS'),(70,4),(0,'ENDSEC'),(0,'SECTION'),(2,'ENTITIES')]
    def line(layer,x1,y1,x2,y2):
        pairs.extend([(0,'LINE'),(100,'AcDbEntity'),(8,layer),(100,'AcDbLine'),(10,x1),(20,y1),(30,0),(11,x2),(21,y2),(31,0)])
    def polyline(layer, corners, bulges=()):
        pairs.extend([(0,'LWPOLYLINE'),(100,'AcDbEntity'),(8,layer),
                      (100,'AcDbPolyline'),(90,len(corners)),(70,1)])
        for index, (x, y) in enumerate(corners):
            pairs.extend([(10,x),(20,y)])
            if bulges and bulges[index]:
                pairs.append((42,bulges[index]))
    outer = face.OuterWire
    for edge in outer.Edges:
        if len(edge.Vertexes)!=2 or not isinstance(edge.Curve, Part.Line):
            raise ValueError('Only straight developed outline edges are supported')
    if closed_polylines:
        polyline('OUTLINE', [(vertex.Point.x,vertex.Point.y) for vertex in outer.OrderedVertexes])
    else:
        for edge in outer.Edges:
            p,q=[v.Point for v in edge.Vertexes]
            line('OUTLINE',p.x,p.y,q.x,q.y)
    for hole in circles:
        if hole.get('profile'):
            for edge in profile_face(hole).OuterWire.Edges:
                start = edge.valueAt(edge.FirstParameter)
                end = edge.valueAt(edge.LastParameter)
                curve = edge.Curve
                if isinstance(curve, Part.Line):
                    line('CUTOUT', start.x, start.y, end.x, end.y)
                    continue
                if curve.Axis.z < 0:
                    start, end = end, start
                center = curve.Center
                angles = [math.degrees(math.atan2(p.y-center.y,p.x-center.x))%360 for p in (start,end)]
                pairs.extend([(0,'ARC'),(100,'AcDbEntity'),(8,'CUTOUT'),(100,'AcDbCircle'),
                              (10,center.x),(20,center.y),(30,0),(40,curve.Radius),
                              (100,'AcDbArc'),(50,angles[0]),(51,angles[1])])
            continue
        if hole.get('polygon') or hole['rect_width']:
            corners = polygon_corners(hole) if hole.get('polygon') else rectangle_corners(hole)
            if closed_polylines:
                polyline('CUTOUT', corners)
            else:
                for a, b in zip(corners, corners[1:]+corners[:1]):
                    line('CUTOUT', *a, *b)
            continue
        if not hole['span']:
            pairs.extend([(0,'CIRCLE'),(100,'AcDbEntity'),(8,'CUTOUT'),(100,'AcDbCircle'),(10,hole['x']),(20,hole['y']),(30,0),(40,hole['radius'])])
            continue
        start, end, direction, normal, radius = slot_profile(hole)
        if closed_polylines:
            points = (start-normal*radius, end-normal*radius,
                      end+normal*radius, start+normal*radius)
            polyline('CUTOUT', [(point.x,point.y) for point in points], (0,1,0,1))
            continue
        for offset in (-radius, radius):
            a, b = start+normal*offset, end+normal*offset
            line('CUTOUT', a.x, a.y, b.x, b.y)
        angle = 90 if hole['vertical'] else 0
        for center, first in ((end, angle-90), (start, angle+90)):
            pairs.extend([(0,'ARC'),(100,'AcDbEntity'),(8,'CUTOUT'),(100,'AcDbCircle'),
                          (10,center.x),(20,center.y),(30,0),(40,radius),
                          (100,'AcDbArc'),(50,first%360),(51,(first+180)%360)])
    for row in bend_rows(flat.Source) if include_bends else []:
        pairs.append((999,'BEND %d SIGNED_ANGLE_DEG %.12g EDGE %s RADIUS_MM %.12g K %.12g'%(row['sequence'],row['angle'],row['edge'],row['radius'],row['k'])))
        line('BEND_CENTER' if row['angle']>0 else 'BEND_CENTER_DOWN',*row['center'])
        pts=row['tangents']
        for a,b in ((pts[0],pts[1]),(pts[2],pts[3])):line('BEND_TANGENTS',*a,*b)
    pairs.extend([(0,'ENDSEC'),(0,'EOF')])
    from pathlib import Path
    target=Path(path)
    if target.suffix.lower()!='.dxf':raise ValueError('Choose a .dxf file')
    with target.open('x',encoding='ascii',newline='\n') as stream:
        stream.write(''.join(str(code)+'\n'+(format(value,'.12g') if isinstance(value,float) else str(value))+'\n' for code,value in pairs))
    return str(target)

def export_bend_table(source,path):
    import csv
    from pathlib import Path
    source=owned(source);source.Document.recompute();rows=bend_rows(source)
    target=Path(path)
    if target.suffix.lower()!='.csv':raise ValueError('Choose a .csv file')
    fields=['Sequence','BaseEdge','Angle_deg','Radius_mm','StraightLength_mm','KFactor','Width_mm','Allowance_mm','CenterX1_mm','CenterY1_mm','CenterX2_mm','CenterY2_mm']
    with target.open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(fields)
        for v in rows:writer.writerow([v['sequence'],v['edge'],v['angle'],v['radius'],v['height'],v['k'],v['width'],v['allowance'],*v['center']])
    return str(target)
