import math
import FreeCAD as App
import MeshPart


def checked(linear, angle):
    """
    Validate and convert linear and angle parameters.
    Returns (linear: float, angle: float).
    Raises ValueError on invalid input.
    """
    if isinstance(linear, bool) or isinstance(angle, bool):
        raise ValueError("Parameters must be numeric, not bool.")
    
    if type(linear) not in (int, float):
        raise ValueError("linear must be a number.")
    if type(angle) not in (int, float):
        raise ValueError("angle must be a number.")

    try:
        linear = float(linear)
        angle = float(angle)
    except (OverflowError, TypeError, ValueError):
        raise ValueError("Conversion to float failed.")

    if not math.isfinite(linear):
        raise ValueError("linear must be finite.")
    if not math.isfinite(angle):
        raise ValueError("angle must be finite.")

    if not (0.01 <= linear <= 1000.0):
        raise ValueError("linear must be between 0.01 and 1000 mm.")
    if not (5.0 <= angle <= 90.0):
        raise ValueError("angle must be between 5 and 90 degrees.")

    return linear, angle


def tessellate(shape, linear, angle):
    """
    Tessellate a Part Shape into a Mesh.
    shape: A valid Part Face, Shell, or Solid (already validated by caller).
    linear: Linear deflection in mm.
    angle: Angular deflection in degrees.
    Returns: A Mesh object.
    Raises ValueError on invalid parameters or mesh validation failure.
    """
    linear, angle = checked(linear, angle)

    try:
        bbox = shape.BoundBox
        diag = math.sqrt(
            (bbox.XMax - bbox.XMin) ** 2 +
            (bbox.YMax - bbox.YMin) ** 2 +
            (bbox.ZMax - bbox.ZMin) ** 2
        )
    except Exception:
        raise ValueError("Invalid shape bounding box.")

    if not math.isfinite(diag):
        raise ValueError("Bounding box diagonal is not finite.")
    
    if diag <= 1e-7:
        raise ValueError("Bounding box diagonal is too small (<= 1e-7).")
    if diag > 10000:
        raise ValueError("Bounding box diagonal is too large (> 10000).")

    if linear < diag / 2000:
        raise ValueError("Linear deflection is too small relative to bounding box diagonal.")

    try:
        shape_copy = shape.copy()
    except Exception:
        raise ValueError("Failed to copy shape.")

    try:
        mesh = MeshPart.meshFromShape(
            Shape=shape_copy,
            LinearDeflection=linear,
            AngularDeflection=math.radians(angle),
            Relative=False
        )
    except Exception:
        raise ValueError("MeshPart.meshFromShape failed.")

    try:
        mesh.Placement = App.Placement()
    except Exception:
        raise ValueError("Failed to reset mesh placement.")

    _validate_mesh(mesh, shape.ShapeType)

    return mesh


def _validate_mesh(mesh, shape_type):
    """
    Validate the generated mesh against specific criteria.
    Raises ValueError if validation fails.
    """
    num_facets = mesh.CountFacets
    if not (1 <= num_facets <= 20000):
        raise ValueError(f"Number of facets ({num_facets}) out of range [1, 20000].")

    vertices = mesh.Topology[0]
    if not vertices:
        raise ValueError("Mesh has no vertices.")
    
    for v in vertices:
        if not math.isfinite(v[0]) or not math.isfinite(v[1]) or not math.isfinite(v[2]):
            raise ValueError("Mesh contains non-finite vertex coordinates.")
        if abs(v[0]) > 1e6 or abs(v[1]) > 1e6 or abs(v[2]) > 1e6:
            raise ValueError("Mesh vertex coordinate exceeds 1e6.")

    try:
        components = mesh.countComponents()
    except AttributeError:
        raise ValueError("Mesh object does not support countComponents.")
    
    if components != 1:
        raise ValueError("Mesh must have exactly one connected component.")

    
    if mesh.hasNonManifolds() or mesh.hasSelfIntersections() or mesh.hasNonUniformOrientedFacets():raise ValueError('Native mesh has invalid topology or orientation')

    for facet in mesh.Facets:
        area = facet.Area
        if not math.isfinite(area) or area <= 1e-12:
            raise ValueError(f"Facet area is invalid: {area}")
        
        normal = facet.Normal
        norm_len = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
        if not (0.99 < norm_len < 1.01):
            raise ValueError(f"Facet normal length is invalid: {norm_len}")

    try:
        is_solid = mesh.isSolid()
    except AttributeError:
        raise ValueError("Mesh object does not support isSolid.")

    if shape_type == 'Solid':
        if not is_solid:
            raise ValueError("Source is Solid but mesh is not closed (isSolid=False).")
    else:
        if is_solid:
            raise ValueError("Source is not Solid but mesh is closed (isSolid=True).")
