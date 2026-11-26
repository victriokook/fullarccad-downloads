import FreeCAD as App
import FreeCADGui as Gui
import Part
from i18n import tr

def toggle(ws):
    sketch = ws.current_sketch()
    if sketch is None or sketch.Document is not App.ActiveDocument:
        raise ValueError(tr("先にスケッチの編集を開始してください。", "Start sketch editing first"))
    if not any(isinstance(g, Part.BSplineCurve) for g in sketch.Geometry):
        raise ValueError(tr("編集中のスケッチにBスプラインがありません。", "The edited sketch has no B-spline"))
    
    if "Sketcher_BSplineComb" not in Gui.listCommands():
        raise ValueError(tr("曲率コームの標準コマンドを利用できません。", "Native curvature comb unavailable"))
    
    Gui.runCommand("Sketcher_BSplineComb", 0)
