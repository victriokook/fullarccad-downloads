"""Whole-surface stitch dialog; fixed kernel sewing, no tolerance control."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_stitch as backend

class StitchDialog(W.QDialog):
    def __init__(self,ws,sources,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=App.ActiveDocument;self.existing=existing
        self.setObjectName('FluxStitchDialog');self.setWindowTitle(tr('面を縫合','Stitch Surfaces'));self.resize(440,420)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('面・殻のオブジェクト全体を選びます（合計2～200面）。閉じた殻はソリッドになります。カーネル既定の許容差で一致する境界のみ対応し、隙間の修復は行いません。','Select whole face/shell objects (2–200 faces). Closed shells become solids. Uses the kernel default sewing tolerance; gap repair is not provided.'));note.setWordWrap(True);layout.addWidget(note)
        self.list=W.QListWidget();layout.addWidget(self.list)
        self.candidates=[]
        for obj in self.doc.Objects:
            if obj==existing or not hasattr(obj,'Shape') or obj.Shape.isNull() or obj.Shape.ShapeType not in ('Face','Shell'):continue
            if existing and existing in obj.OutListRecursive:continue
            self.candidates.append(obj);item=W.QListWidgetItem(obj.Label);item.setData(QtCore.Qt.UserRole,obj.Name)
            item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable);item.setCheckState(QtCore.Qt.Checked if obj in sources else QtCore.Qt.Unchecked);self.list.addItem(item)
        self.initial_stamp=self.stamp();self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.list.itemChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()

    def sources(self):
        return [self.doc.getObject(self.list.item(i).data(QtCore.Qt.UserRole)) for i in range(self.list.count()) if self.list.item(i).checkState()==QtCore.Qt.Checked]
    def stamp(self):
        return (tuple((o.Name,o.Shape.hashCode(),tuple(o.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.parents([o]))) for o in self.candidates),
                (self.existing.Name,tuple(self.existing.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in self.existing.Sources)) if self.existing else None)
    def guard(self):
        if App.ActiveDocument!=self.doc or self.stamp()!=self.initial_stamp:raise ValueError(tr('対象が変わりました。閉じて選び直してください。','The target changed. Close and reselect.'))
    def invalidate(self,*args):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();sources=self.sources();shape=backend.preview(self.doc,sources,self.existing);ExtrudePanel.show_shape(self.host,shape,'new')
            for obj in ([self.existing] if self.existing else sources):self.host.hidden.append((obj,bool(obj.Visibility)));obj.Visibility=False
            self.validated=tuple(o.Name for o in sources);self.ok.setEnabled(True)
            self.status.setText(tr('ソリッドを作成します。','Creates a solid.') if shape.Solids else tr('開いた殻を作成します。','Creates an open shell.'))
        except Exception as error:self.status.setText(str(error))
    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard();sources=self.sources()
            if self.validated!=tuple(o.Name for o in sources):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.apply(self.doc,sources,self.existing)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):
        self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    doc=App.ActiveDocument
    if not doc or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):
        raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx()
    if any(s.SubElementNames or s.Object.Document!=doc for s in selections):raise ValueError(tr('現在の文書の面・殻オブジェクト全体を選択してください。','Select whole surface objects in the current document.'))
    objects=[s.Object for s in selections];existing=objects[0] if len(objects)==1 and getattr(objects[0],'FluxStitch',False) else None
    sources=list(existing.Sources) if existing else objects
    ws.region_picker.ticket+=1;ws.region_picker.clear()
    return StitchDialog(ws,sources,existing).exec()
