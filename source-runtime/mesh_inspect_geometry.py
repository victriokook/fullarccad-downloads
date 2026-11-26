import math

def evaluate(mesh):
    if type(mesh.CountFacets) is not int or not (1 <= mesh.CountFacets <= 20000):
        raise ValueError("CountFacets must be int 1..20000")
    
    m_copy = mesh.copy()
    points, facets = m_copy.Topology
    n = len(points)
    f_count = len(facets)
    
    # Validate coordinates
    for p in points:
        for coord in (p.x, p.y, p.z):
            if not math.isfinite(coord) or abs(coord) > 1e6:
                raise ValueError("Coordinate invalid")

    # Native predicates
    is_solid = m_copy.isSolid()
    has_non_uniform = m_copy.hasNonUniformOrientedFacets()
    has_non_manifold = m_copy.hasNonManifolds()
    has_self_intersect = m_copy.hasSelfIntersections()
    num_components = m_copy.countComponents()

    # Degenerate count
    degenerate_count = 0
    for facet in m_copy.Facets:
        area = facet.Area
        if not math.isfinite(area) or area <= 1e-12:
            degenerate_count += 1
            continue
        norm_len = facet.Normal.Length
        if not math.isfinite(norm_len) or abs(norm_len - 1.0) > 0.01:
            degenerate_count += 1

    # Topology contains index triples; facet objects are m_copy.Facets.
    total_area = math.fsum((points[b]-points[a]).cross(points[c]-points[a]).Length/2 for a,b,c in facets)
    if not math.isfinite(total_area):raise ValueError("Nonfinite area")
    signed_volume = None
    if is_solid and not has_non_uniform and not has_non_manifold and not has_self_intersect and degenerate_count == 0:
        o = points[0]
        signed_volume = math.fsum((points[a]-o).dot((points[b]-o).cross(points[c]-o))/6 for a,b,c in facets)
        if not math.isfinite(signed_volume):raise ValueError("Nonfinite signed volume")

    closed = is_solid
    consistent = not has_non_uniform
    nonmanifold = has_non_manifold
    self_intersection = has_self_intersect

    return {
        "facets": f_count,
        "vertices": n,
        "components": num_components,
        "closed": closed,
        "consistent": consistent,
        "nonmanifold": nonmanifold,
        "self_intersection": self_intersection,
        "degenerate_count": degenerate_count,
        "area": total_area,
        "signed_volume": signed_volume
    }
