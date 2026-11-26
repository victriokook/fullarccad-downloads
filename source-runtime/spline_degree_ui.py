from PySide import QtWidgets as W
import FreeCAD as App
import FreeCADGui as Gui
from i18n import tr
from conic_geometry import signature
import spline_degree as backend
from spline_degree_selection import selected_index

class DegreeDialog(W.QDialog):
    def __init__(self,ws,sketch,index):
        super().__init__(ws.main);self.ws,self.sketch,self.index=ws,sketch,index;self.doc=sketch.Document;self.before=signature(sketch)
        curve=backend.checked(sketch,index);self.setWindowTitle(tr('スプラインの次数を1つ上げる','Increase Spline Degree by One'))
        layout=W.QVBoxLayout(self);layout.addWidget(W.QLabel(tr('次数: %d → %d / 現在の制御点: %d','Degree: %d → %d / Current poles: %d')%(curve.Degree,curve.Degree+1,curve.NbPoles)))
        note=W.QLabel(tr('形状を保って制御点を増やします。周期・非周期の拘束なしのスプライン1本が対象です。形状が変わらないため形状プレビューはありません。','Adds control points while preserving the curve. Applies to one unconstrained periodic or nonperiodic spline. No shape preview is needed because the shape remains unchanged.'));note.setWordWrap(True);layout.addWidget(note)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok)
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
    def accept(self):
        try:
            if App.ActiveDocument is not self.doc or self.doc.getObject(self.sketch.Name) is not self.sketch or self.ws.current_sketch() is not self.sketch or signature(self.sketch)!=self.before:
                raise ValueError(tr('スケッチが変わりました。開き直してください。','The sketch changed. Reopen this dialog.'))
            self.result_degree=backend.elevate(self.sketch,self.index);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    sketch=ws.current_sketch()
    if not sketch or sketch.Document is not App.ActiveDocument or W.QApplication.activeModalWidget():raise ValueError(tr('先にスケッチを編集してください。','Start sketch editing first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].Object is not sketch:raise ValueError(tr('編集中のスプラインの辺を1つ選択してください。','Select one spline edge in the edited sketch.'))
    index=selected_index(list(selected[0].SubElementNames),sketch.GeometryCount);backend.checked(sketch,index)
    return DegreeDialog(ws,sketch,index).exec_()
