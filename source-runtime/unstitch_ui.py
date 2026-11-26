"""Unadopted commit UI; hierarchy-trigger issue still blocks release."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from i18n import tr
from extrude_panel import ExtrudePanel
from unstitch_preview_ui import PreviewDialog
import model_unstitch as backend

class UnstitchDialog(PreviewDialog):
    def __init__(self,ws,source):
        super().__init__(ws,source);self.ws=ws;self.setObjectName('FluxUnstitchDialog');self.setWindowTitle(tr('全ての面を分離','Unstitch All Faces'))
        self.note.setText(tr('全ての面を個別オブジェクトとして分離します。原本は保持して非表示にします。参照形状が変わると分離面を無効化します。','Separate every face into an individual object. Retain and hide the source. Source geometry changes invalidate the separated faces.'))
        self.buttons.setStandardButtons(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False);self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept))
    def compute(self):
        super().compute();self.ok.setEnabled(bool(self.parts) and self.loaded is not None)
    def clear(self):
        super().clear()
        if hasattr(self,'ok'):self.ok.setEnabled(False)
    def accept(self):
        try:
            if App.ActiveDocument!=self.doc or self.loaded is None or self.stamp()!=self.loaded:raise ValueError(tr('先に面を取得してください。','Load faces first.'))
            self.clear();self.result_object=backend.apply(self.doc,self.source);Gui.Selection.clearSelection()
            for obj in self.result_object.Group:Gui.Selection.addSelection(obj)
            self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        W.QDialog.accept(self)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx()
    if len(selections)!=1 or selections[0].SubElementNames:raise ValueError(tr('ソリッドまたは殻全体を1つ選択してください。','Select one whole solid or shell.'))
    source=selections[0].Object;backend.checked(App.ActiveDocument,source);ws.region_picker.ticket+=1;ws.region_picker.clear()
    return UnstitchDialog(ws,source).exec()
