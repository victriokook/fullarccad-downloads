"""Planar spiral path; local-Qwen scalar proposal reviewed before use."""
import math
from functools import lru_cache

def end_radius(radius, growth, turns):
    for value in (radius,growth,turns):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError('Expected finite numeric inputs')
    if radius<=0 or growth<=0 or not .25<=turns<=50:
        raise ValueError('Invalid spiral dimensions')
    result=radius+growth*turns
    if not math.isfinite(result):raise ValueError('Spiral radius overflow')
    return result

@lru_cache(maxsize=8)
def _spine(radius,growth,turns,left):
    import FreeCAD as App
    import Part
    end_radius(radius,growth,turns)
    active=App.ActiveDocument
    doc=App.newDocument('FluxSpiralGenerator','',True,True)
    try:
        obj=doc.addObject('Part::Spiral','Path')
        obj.Radius=radius;obj.Growth=growth;obj.Rotations=turns
        doc.recompute()
        wire=Part.Wire(obj.Shape.Edges)
        if wire.isNull() or not wire.isValid():raise ValueError('Invalid spiral path')
        if left:wire.rotate(App.Vector(),App.Vector(1,0,0),180)
        return wire
    finally:
        App.closeDocument(doc.Name)
        if active and App.ActiveDocument!=active:App.setActiveDocument(active.Name)

def spine(radius,growth,turns,left=False):
    return _spine(radius,growth,turns,bool(left)).copy()
