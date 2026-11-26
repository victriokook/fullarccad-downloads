"""One-surface native reverse operation with transient preview and Cancel."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import reverse_surface as backend

class ReverseDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.doc=source.Document
        self.setObjectName('FluxReverseNormal');self.setWindowTitle(tr('法線を反転','Reverse Normal'))
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=False;self.initial_stamp=self.stamp()
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('対象: %s\n面・殻全体の正負の向きを反転します。形状と面積は変えません。元のサーフェスを保持し、FreeCAD標準の反転履歴を作成します。','Surface: %s\nReverses the whole face/shell orientation without changing its geometry or area. Retains the source and creates a native FreeCAD reverse feature.')%source.Label);note.setWordWrap(True);layout.addWidget(note)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def stamp(self):return self.source.Shape.hashCode(),tuple(self.source.getGlobalPlacement().toMatrix().A)
    def guard(self):
        if App.ActiveDocument!=self.doc or self.doc.getObject(self.source.Name)!=self.source or self.stamp()!=self.initial_stamp:raise ValueError(tr('対象が変わりました。選び直してください。','The target changed. Reselect it.'))
    def invalidate(self):
        ExtrudePanel.clear_preview(self.host);self.validated=False;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.source);ExtrudePanel.show_shape(self.host,shape,'new')
            self.host.hidden.append((self.source,bool(self.source.Visibility)));self.source.Visibility=False
            self.validated=True;self.ok.setEnabled(True);self.status.setText(tr('全%d面の法線を反転します。面積: %.6g mm²','Reverse normals of all%d faces. Area: %.6g mm²')%(len(shape.Faces),shape.Area))
        except Exception as error:self.status.setText(str(error))
    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if not self.validated:raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.create(self.doc,self.source)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx()
    if len(selections)!=1 or selections[0].SubElementNames:raise ValueError(tr('面または殻のオブジェクト全体を1つ選択してください。','Select one whole face or shell object.'))
    source=selections[0].Object;backend.preview(source);ws.region_picker.ticket+=1;ws.region_picker.clear()
    return ReverseDialog(ws,source).exec()
