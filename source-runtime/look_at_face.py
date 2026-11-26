"""Look at one planar face using the native camera alignment command."""
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtWidgets as W
from i18n import tr
from look_at_face_index import face_index

def show(ws):
    doc=App.ActiveDocument
    if not doc or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(value,'active',False) is True for value in vars(ws).values()):
        raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active edit.'))
    selection=Gui.Selection.getSelectionEx()
    if len(selection)!=1 or selection[0].Object.Document is not doc or len(selection[0].SubElementNames)!=1:
        raise ValueError(tr('現在の文書で平面を1面だけ選択してください。','Select exactly one planar face in the current document.'))
    obj=selection[0].Object
    if not hasattr(obj,'Shape') or obj.isDerivedFrom('App::Link'):raise ValueError('Select a shape face; links are excluded.')
    shape=obj.Shape;index=face_index(selection[0].SubElementNames[0],len(shape.Faces));face=shape.Faces[index]
    if face.isNull() or not face.isValid() or not isinstance(face.Surface,Part.Plane):raise ValueError(tr('曲面は対象外です。平面を選択してください。','Curved faces are excluded. Select a planar face.'))
    view=Gui.activeDocument().activeView()
    if not hasattr(view,'getCameraNode') or 'Std_AlignToSelection' not in Gui.listCommands():raise ValueError('Native3D camera alignment is unavailable.')
    old=view.getCamera();animation=view.isAnimationEnabled()
    try:
        view.setAnimationEnabled(False);Gui.runCommand('Std_AlignToSelection')
    except Exception:
        view.setCamera(old);raise
    finally:view.setAnimationEnabled(animation)
    ws.grid.update()
