"""Native Draft text faces and a native extrusion; no custom recompute proxy."""
from pathlib import Path
import xml.etree.ElementTree as ET
import FreeCAD as App
from i18n import tr
import model
from solid_text_values import validate_text_values


def validate(text, font, size, tracking, depth):
    values = validate_text_values(text, size, tracking, depth)
    if not isinstance(font, str) or not font or '\x00' in font:
        raise ValueError(tr('ローカルのフォントファイルを指定してください。', 'Specify a local font file.'))
    path = Path(font)
    if not path.is_file() or path.suffix.lower() not in ('.ttf', '.otf', '.ttc'):
        raise ValueError(tr('既存のTTF/OTF/TTCフォントを指定してください。', 'Specify an existing TTF/OTF/TTC font.'))
    if any(ord(char)>126 for char in text):
        try:
            from fontTools.ttLib import TTFont
            with TTFont(str(path),lazy=True,fontNumber=0 if path.suffix.lower()=='.ttc' else -1) as font_data:
                cmap=font_data.getBestCmap() or {}
                missing=[char for char in set(text) if not char.isspace() and
                         (ord(char) not in cmap or font_data.getGlyphID(cmap[ord(char)])==0)]
            if missing:
                raise ValueError(tr('フォントに字形がありません: ', 'Font is missing glyphs: ')+''.join(sorted(missing)))
        except ValueError:raise
        except Exception as error:
            raise ValueError(tr('フォントの日本語字形を確認できません。別のTTF/OTF/TTCを指定してください。',
                                'Cannot check Japanese glyphs. Choose another TTF/OTF/TTC font.')) from error
    if any(ord(char)>126 for char in text):
        import Part
        for char in sorted(set(text)):
            if char.isspace():continue
            try:
                glyphs=Part.makeWireString(char,str(path),values[1],0)
                faces=Part.makeFace(glyphs[0],"Part::FaceMakerBullseye")
                if faces.isNull() or not faces.isValid() or not faces.Faces or faces.Area<=1e-12:raise ValueError()
            except Exception as error:
                raise ValueError(tr('字形を有効な面にできません。フォントを変更してください: ',
                                    'Glyph cannot form valid faces. Choose another font: ')+char) from error
    return values, str(path.resolve())


def is_text(obj):
    return bool(obj and getattr(obj, 'FluxSolidText', False)
                and obj.TypeId == 'Part::Extrusion' and obj.Base
                and getattr(getattr(obj.Base, 'Proxy', None), 'Type', '') == 'ShapeString')


def stamp(obj):
    if not is_text(obj):
        return None
    def inputs(item):
        root = ET.fromstring('<Root>'+item.Content+'</Root>')
        for props in root.iter('Properties'):
            for prop in list(props):
                if prop.attrib.get('name') in ('Shape', 'Visibility'):
                    props.remove(prop)
        return ET.tostring(root, encoding='unicode')
    shape = obj.Shape
    bb = shape.BoundBox
    geometry = (len(shape.Solids), len(shape.Faces), round(shape.Volume, 7),
                round(shape.Area, 7), tuple(round(v, 7) for v in
                (bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax)))
    return (inputs(obj), inputs(obj.Base), geometry)


def _build(doc, text, font, size, tracking, depth, existing=None, alignment=None, reference=None):
    if existing is None:
        from draftobjects.shapestring import ShapeString
        from draftviewproviders.view_shapestring import ViewProviderShapeString
        source = doc.addObject('Part::Part2DObjectPython', 'TextOutline')
        ShapeString(source)
        ViewProviderShapeString(source.ViewObject)
        source.Label = tr('文字輪郭', 'Text Outline')
        out = doc.addObject('Part::Extrusion', 'SolidText')
        out.addProperty('App::PropertyBool', 'FluxSolidText', 'FluxCAD').FluxSolidText = True
        out.setEditorMode('FluxSolidText', 2)
        out.Base = source
        out.Label = tr('文字ソリッド', 'Solid Text')
    else:
        out, source = existing, existing.Base
    from text_alignment_values import checked_alignment
    alignment,reference=checked_alignment(alignment,reference)
    if alignment is not None:source.Justification=alignment
    if reference is not None:source.JustificationReference=reference
    source.String, source.FontFile = text, font
    source.Size, source.Tracking = size, tracking
    out.Dir = App.Vector(0, 0, depth)
    out.Solid = True
    doc.recompute()
    if (source.Shape.isNull() or not source.Shape.isValid() or not source.Shape.Faces
            or out.Shape.isNull() or not out.Shape.isValid() or not out.Shape.Solids
            or out.Shape.Volume <= 1e-9 or len(out.Shape.Solids) > 1000
            or any(state in out.State for state in ('Invalid', 'Error'))):
        raise ValueError(tr('文字をソリッドにできません。フォント・間隔・厚さを確認してください。',
                            'Cannot form text solids. Check the font, spacing and thickness.'))
    source.Visibility = False
    return out


def create(doc, text, font, size, tracking, depth, existing=None, alignment=None, reference=None):
    from text_alignment_values import checked_alignment
    alignment,reference=checked_alignment(alignment,reference)
    values, font = validate(text, font, size, tracking, depth)
    if App.ActiveDocument is not doc:
        raise ValueError('The active document changed')
    if existing is not None and (not is_text(existing) or existing.Document is not doc):
        raise ValueError('Select a Solid Text result')
    dependents = [(o, bool(o.Shape.Solids)) for o in existing.InListRecursive
                  if hasattr(o, 'Shape') and not o.Shape.isNull() and o.Shape.isValid()] if existing else []
    with model.transaction(doc, tr('文字ソリッド', 'Solid Text')):
        out = _build(doc, values[0], font, *values[1:], existing=existing,alignment=alignment,reference=reference)
        if any(o.Shape.isNull() or not o.Shape.isValid() or (solid and not o.Shape.Solids)
               or any(state in o.State for state in ('Error', 'Invalid')) for o, solid in dependents):
            raise ValueError(tr('後の加工を更新できないため編集を取り消しました。',
                                'A dependent feature could not update; the edit was undone.'))
    return out


def preview(doc, text, font, size, tracking, depth, existing=None, alignment=None, reference=None):
    from text_alignment_values import checked_alignment
    alignment,reference=checked_alignment(alignment,reference)
    values, font = validate(text, font, size, tracking, depth)
    if App.ActiveDocument is not doc:
        raise ValueError('The active document changed')
    doc.openTransaction('Solid Text preview')
    try:
        if existing is not None:
            if alignment is None:alignment=str(existing.Base.Justification)
            if reference is None:reference=str(existing.Base.JustificationReference)
        out = _build(doc, values[0], font, *values[1:],alignment=alignment,reference=reference)
        shape = out.Shape.copy()
        if existing is not None:
            shape.Placement = existing.getGlobalPlacement()
        return shape
    finally:
        doc.abortTransaction()
        doc.recompute()
