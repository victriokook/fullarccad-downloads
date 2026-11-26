from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from i18n import tr
from extrude_panel import ExtrudePanel
import model_all_edges_fillet as backend

class AllEdgesFilletDialog(W.QDialog):
    def __init__(self,ws,source,existing=None):
        super().__init__(ws.main)
        self.ws,self.source,self.existing,self.doc=ws,source,existing,App.ActiveDocument
        self.initial_stamp=backend.stamp(source,existing)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.setObjectName('FluxAllEdgesFillet');self.setWindowTitle(tr('全辺フィレット','All Edges Fillet'))
        form=W.QFormLayout(self);form.addRow(tr('原本','Source'),W.QLabel(source.Label))
        self.radius=W.QDoubleSpinBox();self.radius.setDecimals(8);self.radius.setRange(.001,100000);self.radius.setSuffix(' mm')
        self.original=existing.Input.FilletRadius if existing else 1.;self.radius.setValue(self.original);self.display=self.radius.value()
        form.addRow(tr('半径','Radius'),self.radius)
        note=W.QLabel(tr('単一ソリッドの全ての適用可能な辺を同じ半径で丸めます。原本の辺数変更に追従します。失敗する場合は半径を小さくしてください。', 'Rounds all applicable edges of one solid with one radius. Follows changes to the source edge count. Reduce the radius if the native operation fails.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.radius.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
    def value(self):return self.original if self.radius.value()==self.display else self.radius.value()
    def guard(self):
        if App.ActiveDocument is not self.doc or self.ws.current_sketch() or self.doc.getObject(self.source.Name) is not self.source or (self.existing and self.doc.getObject(self.existing.Name) is not self.existing) or backend.stamp(self.source,self.existing)!=self.initial_stamp:
            raise ValueError(tr('文書または対象が変わりました。開き直してください。','The document or target changed. Reopen this dialog.'))
    def invalidate(self,*_):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.doc,self.source,self.value(),self.existing)
            ExtrudePanel.show_shape(self.host,shape,'new')
            if self.existing:self.host.hidden.append((self.existing,bool(self.existing.Visibility)));self.existing.Visibility=False
            self.validated=self.value();self.ok.setEnabled(True);self.status.setText(tr('体積: %.6g mm³','Volume: %.6g mm³')%shape.Volume)
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated!=self.value():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.apply(self.doc,self.source,self.value(),self.existing)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('文書を開き、現在の編集を終了してください。','Open a document and finish the current edit.'))
    selected=Gui.Selection.getSelection()
    if len(selected)!=1:raise ValueError(tr('ソリッドを1つ選択してください。','Select one solid body.'))
    existing=selected[0] if getattr(selected[0],'FluxAllEdgesFillet',False) else None
    source=existing.Source if existing else selected[0];backend.validate(App.ActiveDocument,source,existing);backend.checked_source(source)
    return AllEdgesFilletDialog(ws,source,existing).exec_()
