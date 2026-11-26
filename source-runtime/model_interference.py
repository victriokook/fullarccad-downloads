"""Read-only, world-space solid interference checks using OpenCASCADE booleans."""
import math
from itertools import combinations
import browser
from i18n import tr


def candidates(doc):
    return browser.collect(doc)[0] if doc else []


def visible(obj):
    current = obj
    while current:
        if not getattr(current, 'Visibility', True):
            return False
        current = current.getParentGeoFeatureGroup()
    return True


def snapshot(doc):
    """Detect edits, deletion, undo, visibility and parent-placement changes."""
    rows = []
    for obj, title in candidates(doc):
        states = tuple((o.Name, tuple(o.State), getattr(o, 'Error', ''),
                        getattr(o, 'AssemblyError', '')) for o in [obj]+obj.OutListRecursive)
        shape = obj.Shape
        rows.append((obj.Name, obj.Label, None if shape.isNull() else shape.hashCode(), str(obj.getGlobalPlacement()),
                     visible(obj), states))
    return tuple(rows)


def prepare(doc, objects, minimum=0.000001):
    if not math.isfinite(minimum) or minimum < 0:
        raise ValueError(tr('最小体積を0以上にしてください。', 'Minimum volume must be nonnegative.'))
    allowed = {o.Name for o, title in candidates(doc)}
    objects = list(dict.fromkeys(browser.body_owner(o) for o in objects))
    if not 2 <= len(objects) <= 100:
        raise ValueError(tr('検査するボディを2〜100個指定してください。', 'Choose between 2 and 100 bodies to inspect.'))
    from model_combine import solid
    entries = []
    for obj in objects:
        if obj.Document != doc or obj.Name not in allowed:
            raise ValueError(tr('現在の文書のブラウザーにあるボディを選択してください。',
                                'Select current browser bodies in this document.'))
        if any('Touched' in o.State for o in [obj]+obj.OutListRecursive):
            raise ValueError(tr('「%s」は未再計算です。再計算してから検査してください。',
                                '"%s" needs recomputing before inspection.') % obj.Label)
        for source in [obj]+obj.OutListRecursive:
            error = getattr(source, 'Error', '') or getattr(source, 'AssemblyError', '')
            if error:
                raise ValueError(source.Label+': '+str(error))
        try:
            shape = solid(obj)
            # A pattern/compound may contain overlapping solids. Measure the
            # material union, rather than counting duplicated material twice.
            if len(shape.Solids) > 1:
                parts = shape.Solids
                shape = parts[0].multiFuse(parts[1:]).removeSplitter()
            if shape.isNull() or not shape.isValid() or not shape.Solids:
                raise ValueError(tr('有効な立体として検査できません。', 'Cannot inspect this as a valid solid.'))
        except Exception as error:
            raise ValueError(obj.Label+': '+str(error)) from error
        entries.append(dict(name=obj.Name, label=obj.Label, shape=shape, bounds=shape.BoundBox))
    return entries


def pairs(entries):
    return combinations(entries, 2)


def check_pair(first, second, minimum=0.000001, include_contacts=False):
    if type(include_contacts) is not bool:raise ValueError("Expected boolean Include Coincident Faces")
    a, b = first['bounds'], second['bounds']
    # A disjoint box or zero-width intersection cannot contain shared volume.
    widths=[min(getattr(a, axis+'Max'), getattr(b, axis+'Max'))-max(getattr(a, axis+'Min'), getattr(b, axis+'Min')) for axis in ('X','Y','Z')]
    if any(width<0 if include_contacts else width<=0 for width in widths):
        return None
    overlap = first['shape'].common(second['shape'])
    if overlap.isNull() or not overlap.Solids:
        if not include_contacts:return None
        import Part
        from coincident_face_area import contact_area
        shared=Part.makeCompound(first['shape'].Faces).common(Part.makeCompound(second['shape'].Faces))
        if shared.isNull() or not shared.Faces:return None
        if not shared.isValid() or shared.Solids:raise ValueError('Shared face calculation is invalid')
        area=contact_area(len(shared.Faces),shared.Area)
        if area is None:return None
        return dict(first=first['name'],second=second['name'],labels=(first['label'],second['label']),volume=0.,area=area,kind='coincident_face',shape=shared)
    if not overlap.isValid():
        raise ValueError(tr('交差形状の計算に失敗しました。', 'The intersection is not a valid shape.'))
    volume = overlap.Volume
    if not math.isfinite(volume) or volume < 0:
        raise ValueError(tr('交差体積を求められません。', 'Cannot measure the intersection volume.'))
    if volume <= max(1e-9, minimum):
        return None
    return dict(first=first['name'], second=second['name'],
                labels=(first['label'], second['label']), volume=volume, shape=overlap)
