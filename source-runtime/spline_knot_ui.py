from PySide import QtWidgets as W
import FreeCAD as App
import FreeCADGui as Gui
from i18n import tr
from conic_geometry import signature
import spline_knot as backend
from spline_degree_selection import selected_index

class KnotDialog(W.QDialog):
    def __init__(self,ws,sketch,index):
        super().__init__(ws.main);self.ws,self.sketch,self.index=ws,sketch,index;self.doc=sketch.Document;self.before=signature(sketch)
        curve=backend.checked(sketch,index);self.setWindowTitle(tr('スプラインに制御点を追加','Insert Spline Control Point'))
        layout=W.QVBoxLayout(self);layout.addWidget(W.QLabel(tr('次数: %d / 制御点: %d → %d','Degree: %d / Poles: %d → %d')%(curve.Degree,curve.NbPoles,curve.NbPoles+1)))
        self.fraction=W.QDoubleSpinBox();self.fraction.setDecimals(8);self.fraction.setRange(.001,.999);self.fraction.setValue(.5);layout.addWidget(self.fraction)
        note=W.QLabel(tr('位置は曲線パラメータの比率0.001～0.999です（弧長比率ではありません）。新しいノットを1個挿入し、形状を保持します。既存ノット位置・拘束付き曲線は対象外です。','Position is a curve-parameter fraction0.001–0.999, rather than an arc-length fraction. Inserts one new knot while preserving shape. Existing knots and constrained splines are excluded.'));note.setWordWrap(True);layout.addWidget(note)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok)
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
    def accept(self):
        try:
            if App.ActiveDocument is not self.doc or self.doc.getObject(self.sketch.Name) is not self.sketch or self.ws.current_sketch() is not self.sketch or signature(self.sketch)!=self.before:
                raise ValueError(tr('スケッチが変わりました。開き直してください。','The sketch changed. Reopen this dialog.'))
            self.result_poles=backend.insert(self.sketch,self.index,self.fraction.value());self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    sketch=ws.current_sketch()
    if not sketch or sketch.Document is not App.ActiveDocument or W.QApplication.activeModalWidget():raise ValueError(tr('先にスケッチを編集してください。','Start sketch editing first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].Object is not sketch:raise ValueError(tr('編集中のスプラインの辺を1つ選択してください。','Select one spline edge in the edited sketch.'))
    index=selected_index(list(selected[0].SubElementNames),sketch.GeometryCount);backend.checked(sketch,index)
    return KnotDialog(ws,sketch,index).exec_()
