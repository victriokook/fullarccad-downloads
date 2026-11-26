"""Coordinate entry for an exact conic in the currently edited sketch."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from i18n import tr
import conic_geometry


def show(ws):
    sketch = ws.current_sketch()
    if sketch is None:
        raise ValueError(tr('先にスケッチの編集を開始してください。', 'Start sketch editing first.'))
    doc, name = sketch.Document, sketch.Name
    ws.select_sketch_geometry()
    stamp = conic_geometry.signature(sketch)
    dialog = W.QDialog(ws.main)
    dialog.setObjectName('FluxConicCurve')
    dialog.setWindowTitle(tr('円錐曲線', 'Conic Curve'))
    dialog.setMinimumWidth(440)
    form = W.QFormLayout(dialog)
    fields = []
    for key, label, default in (
            ('StartX', tr('始点 X', 'Start X'), 0),
            ('StartY', tr('始点 Y', 'Start Y'), 0),
            ('EndX', tr('終点 X', 'End X'), 10),
            ('EndY', tr('終点 Y', 'End Y'), 0),
            ('VertexX', tr('接線交点 X', 'Tangent intersection X'), 5),
            ('VertexY', tr('接線交点 Y', 'Tangent intersection Y'), 10),
            ('Rho', 'Rho', .5)):
        field = W.QDoubleSpinBox()
        field.setObjectName('FluxConic'+key)
        field.setDecimals(9)
        field.setRange(.001, .999) if key == 'Rho' else field.setRange(-1e6, 1e6)
        if key != 'Rho':
            field.setSuffix(' mm')
        field.setValue(default)
        fields.append(field)
        form.addRow(label, field)
    construction = W.QCheckBox(tr('補助図形', 'Construction geometry'))
    construction.setObjectName('FluxConicConstruction')
    form.addRow(construction)
    note = W.QLabel(tr(
        '座標はスケッチ平面内です。接線交点は曲線上の点ではありません。Rho < 0.5：楕円、0.5：放物線、> 0.5：双曲線。追加後は標準Bスプラインとして編集できます。',
        'Coordinates are local to the sketch plane. The tangent intersection is not a point on the curve. Rho < 0.5: ellipse; 0.5: parabola; > 0.5: hyperbola. Edit the result as a standard B-spline.'))
    note.setWordWrap(True)
    form.addRow(note)
    status = W.QLabel()
    status.setObjectName('FluxConicStatus')
    status.setWordWrap(True)
    form.addRow(status)
    preview = W.QPushButton(tr('プレビュー', 'Preview'))
    preview.setObjectName('FluxConicPreview')
    form.addRow(preview)
    buttons = W.QDialogButtonBox(W.QDialogButtonBox.Ok | W.QDialogButtonBox.Cancel)
    form.addRow(buttons)
    scene = Gui.activeDocument().activeView().getSceneGraph()
    node = [None]

    def clear():
        if node[0] is not None:
            scene.removeChild(node[0])
            node[0] = None

    def guard():
        if (App.ActiveDocument is not doc or doc.getObject(name) is not sketch
                or ws.current_sketch() is not sketch or conic_geometry.signature(sketch) != stamp):
            raise ValueError(tr('スケッチが変わりました。画面を開き直してください。',
                                'The sketch changed. Reopen this dialog.'))

    def values():
        v = [f.value() for f in fields]
        return (tuple(v[:2]), tuple(v[2:4]), tuple(v[4:6]), v[6])

    def update_preview():
        clear()
        try:
            guard()
            geometry = conic_geometry.curve(*values())
            from pivy import coin
            points = [sketch.getGlobalPlacement().multVec(p) for p in geometry.toShape().discretize(100)]
            group = coin.SoSeparator()
            color = coin.SoBaseColor()
            color.rgb = (1., .65, .1)
            coords = coin.SoCoordinate3()
            coords.point.setValues(0, len(points), [tuple(p) for p in points])
            line = coin.SoLineSet()
            line.numVertices.setValue(len(points))
            for child in (color, coords, line):
                group.addChild(child)
            scene.addChild(group)
            node[0] = group
            status.setText(tr('プレビューを表示しました。', 'Preview displayed.'))
        except Exception as error:
            status.setText(str(error))

    def accept():
        try:
            guard()
            conic_geometry.add(sketch, *values(), construction=construction.isChecked())
            dialog.accept()
        except Exception as error:
            clear()
            status.setText(str(error))

    preview.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(update_preview))
    for field in fields:
        field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda *_: clear(),(0, 0, True, False)))
    buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(accept))
    buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(dialog.reject))
    try:
        dialog.exec_()
    finally:
        clear()
    ws.refresh()
