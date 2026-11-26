from PySide import QtWidgets as W
import FreeCAD as App
import FreeCADGui as Gui
from i18n import tr
from conic_geometry import signature
import spline_reduce as backend
from spline_degree_selection import selected_index

class ReductionDialog(W.QDialog):
    def __init__(self,ws,sketch,index):
        super().__init__(ws.main);self.ws,self.sketch,self.index=ws,sketch,index;self.doc=sketch.Document;self.before=signature(sketch)
        curve=backend.checked(sketch,index);self.setWindowTitle(tr('スプラインの次数を1つ下げる','Decrease Spline Degree by One'))
        layout=W.QVBoxLayout(self);layout.addWidget(W.QLabel(tr('次数: %d → %d / 現在の制御点: %d','Degree: %d → %d / Current poles: %d')%(curve.Degree,curve.Degree-1,curve.NbPoles)))
        self.limit=W.QDoubleSpinBox();self.limit.setDecimals(6);self.limit.setRange(.000001,10);self.limit.setValue(.1);self.limit.setSuffix(' mm');layout.addWidget(W.QLabel(tr('測定点の変位上限','Sampled Displacement Limit')));layout.addWidget(self.limit)
        note=W.QLabel(tr('近似により形状・連続性が変わり、制御点が増える場合があります。1025等間隔点とノット・中点で変位を確認します。全曲線の誤差保証ではありません。形状プレビューはありません。Undoで戻せます。非周期・拘束なし、次数2～9、制御点50以下が対象です。','Approximation changes shape and continuity and may add control points. Checks displacement at1025 uniform parameter samples plus knots and midpoints; this is not a global error guarantee. No shape preview. Undo restores the curve. Nonperiodic, unconstrained splines of degree2–9 with at most50 poles only.'));note.setWordWrap(True);layout.addWidget(note)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok)
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
    def accept(self):
        try:
            if App.ActiveDocument is not self.doc or self.doc.getObject(self.sketch.Name) is not self.sketch or self.ws.current_sketch() is not self.sketch or signature(self.sketch)!=self.before:
                raise ValueError(tr('スケッチが変わりました。開き直してください。','The sketch changed. Reopen this dialog.'))
            self.reduction_result=backend.reduce(self.sketch,self.index,self.limit.value());self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    sketch=ws.current_sketch()
    if not sketch or sketch.Document is not App.ActiveDocument or W.QApplication.activeModalWidget():raise ValueError(tr('先にスケッチを編集してください。','Start sketch editing first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].Object is not sketch:raise ValueError(tr('編集中のスプラインの辺を1つ選択してください。','Select one spline edge in the edited sketch.'))
    index=selected_index(list(selected[0].SubElementNames),sketch.GeometryCount);backend.checked(sketch,index)
    return ReductionDialog(ws,sketch,index).exec_()
