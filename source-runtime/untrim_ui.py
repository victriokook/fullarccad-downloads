"""One-surface native reverse operation with transient preview and Cancel."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_untrim as backend

class UntrimDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.doc=source.Document
        self.setObjectName('FluxInternalUntrim');self.setWindowTitle(tr('面の内側穴を埋める','Fill Internal Surface Holes'))
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=False;self.initial_stamp=self.stamp()
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('対象: %s\n内側の穴を全て埋め、外周と面の向きを保持します。外側の切欠き・外周延長は対象外です。元の面は保持して非表示にします。','Surface: %s\nFills all internal holes while preserving the outer boundary and orientation. Exterior notches and outer extensions are excluded. Retains and hides the source.')%source.Label);note.setWordWrap(True);layout.addWidget(note)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def stamp(self):return self.source.Shape.hashCode(),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(self.source)),getattr(self.source,'Error','')
    def guard(self):
        if App.ActiveDocument!=self.doc or self.doc.getObject(self.source.Name)!=self.source or self.stamp()!=self.initial_stamp:raise ValueError(tr('対象が変わりました。選び直してください。','The target changed. Reselect it.'))
    def invalidate(self):
        ExtrudePanel.clear_preview(self.host);self.validated=False;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.doc,self.source);ExtrudePanel.show_shape(self.host,shape,'new')
            self.host.hidden.append((self.source,bool(self.source.Visibility)));self.source.Visibility=False
            self.validated=True;self.ok.setEnabled(True);self.status.setText(tr('内側穴を埋めます。面積: %.6g mm²','Fill internal holes. Area: %.6g mm²')%shape.Area)
        except Exception as error:self.status.setText(str(error))
    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if not self.validated:raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.apply(self.doc,self.source)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx()
    if len(selections)!=1 or selections[0].SubElementNames:raise ValueError(tr('1枚の面のオブジェクト全体を選択してください。','Select one whole single-face object.'))
    source=selections[0].Object;backend.preview(source.Document,source);ws.region_picker.ticket+=1;ws.region_picker.clear()
    return UntrimDialog(ws,source).exec()
