import math
import FreeCAD as App


def checked_angles(angle_x=0,angle_y=0):
    values=[]
    for value in (angle_x,angle_y):
        if type(value) not in (int,float):raise ValueError('Angle must be an exact int or float')
        try:value=float(value)
        except (ValueError,TypeError,OverflowError):raise ValueError('Invalid angle')
        if not math.isfinite(value) or abs(value)>180:raise ValueError('Angle must be finite and within ±180 degrees')
        values.append(value)
    return tuple(values)

def tilted_frame(plane, position, angle_x=0, angle_y=0):
    """
    Compute a tilted placement frame for mesh sectioning.
    
    The pivot is the original world coordinate-axis point:
    - For XY plane: pivot is (0, 0, position)
    - For XZ plane: pivot is (0, position, 0)
    - For YZ plane: pivot is (position, 0, 0)
    
    Rotations are applied about the original guiding frame axes (extrinsic),
    not successive intrinsic axes. No equivalence to Autodesk rotation-sign conventions is guaranteed.
    
    Args:
        plane: The XY/XZ/YZ guiding-plane string.
        position: The signed world-axis position in mm.
        angle_x: Rotation around X axis in degrees.
        angle_y: Rotation around Y axis in degrees.
        
    Returns:
        App.Placement with modified Rotation, unchanged Base.
    """
    angle_x, angle_y = checked_angles(angle_x, angle_y)
    
    import mesh_section_geometry
    
    original_frame = mesh_section_geometry.frame(plane, position)
    
    if angle_x == 0 and angle_y == 0:
        return original_frame
    
    rot_y = App.Rotation(App.Vector(0, 1, 0), angle_y)
    rot_x = App.Rotation(App.Vector(1, 0, 0), angle_x)
    tilted_rotation = original_frame.Rotation.multiply(rot_y).multiply(rot_x)
    
    base = original_frame.Base
    if not (math.isfinite(base.x) and math.isfinite(base.y) and math.isfinite(base.z)):
        raise ValueError("Original frame Base is not finite")
    
    if abs(base.x) > 1e6 or abs(base.y) > 1e6 or abs(base.z) > 1e6:
        raise ValueError("Original frame Base exceeds bounds +-1e6")
    
    quat = tilted_rotation.Q
    if not (math.isfinite(quat[0]) and math.isfinite(quat[1]) and 
            math.isfinite(quat[2]) and math.isfinite(quat[3])):
        raise ValueError("Tilted rotation quaternion is not finite")
    
    basis=[tilted_rotation.multVec(v) for v in (App.Vector(1,0,0),App.Vector(0,1,0),App.Vector(0,0,1))]
    if any(not math.isfinite(c) for v in basis for c in v):raise ValueError('Non-finite rotation basis')
    for i,a in enumerate(basis):
        for j,b in enumerate(basis):
            if abs(a.dot(b)-(1.0 if i==j else 0.0))>1e-10:raise ValueError('Non-orthonormal rotation basis')
    new_placement = App.Placement()
    new_placement.Base = base
    new_placement.Rotation = tilted_rotation
    
    return new_placement


def section_data(mesh, pose, plane, position, angle_x=0, angle_y=0):
    """
    Get section data for a mesh with optional tilt.
    
    Uses mesh_section_geometry.section_data for actual computation.
    If both angles are zero, calls the original section_data unchanged.
    Otherwise, constructs a tilted frame and passes it as placement keyword.
    
    The helper does all actual native mesh.crossSections, full parent/own source-local cutting,
    world/sketch finite/bounds, float32 residual, XYround6 snap, undirected segment dedup,
    500segments/50groups/graph-degree<=2 guards.
    
    Args:
        mesh: The mesh object.
        pose: The pose.
        plane: The XY/XZ/YZ guiding-plane string.
        position: The signed world-axis position in mm.
        angle_x: Rotation around X axis in degrees.
        angle_y: Rotation around Y axis in degrees.
        
    Returns:
        Existing tuple(segments, placement).
    """
    angle_x, angle_y = checked_angles(angle_x, angle_y)
    
    import mesh_section_geometry
    
    if angle_x == 0 and angle_y == 0:
        return mesh_section_geometry.section_data(mesh, pose, plane, position)
    
    tilted_frame_obj = tilted_frame(plane, position, angle_x, angle_y)
    
    return mesh_section_geometry.section_data(mesh, pose, plane, position, placement=tilted_frame_obj)
