"""Count guard only; geometric connectivity is checked separately."""


def validate_wire_vertices(edges, vertices, closed):
    if type(edges) is not int or type(vertices) is not int or type(closed) is not bool:
        raise ValueError('Use exact integer counts and boolean closure')
    if not 1 <= edges <= 200 or vertices != (edges if closed else edges+1):
        raise ValueError('Wire must have1..200 edges without repeated vertices')
    return None
