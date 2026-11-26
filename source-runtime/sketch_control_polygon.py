import FreeCAD as App
import FreeCADGui as Gui
import Part
from i18n import tr


def toggle(ws):
    sketch = ws.current_sketch()
    if sketch is None or sketch.Document is not App.ActiveDocument:
        raise ValueError(tr('先にスケッチの編集を開始してください。', 'Start sketch editing first.'))
    if not any(isinstance(g, Part.BSplineCurve) for g in sketch.Geometry):
        raise ValueError(tr('編集中のスケッチにBスプラインがありません。', 'The edited sketch has no B-spline.'))
    if 'Sketcher_BSplinePolygon' not in Gui.listCommands():
        raise ValueError(tr('制御ポリゴンの標準コマンドを利用できません。', 'Native control polygon display is unavailable.'))
    Gui.runCommand('Sketcher_BSplinePolygon', 0)
