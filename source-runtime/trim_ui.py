"""Explicit list-based trim region selection and stale-preview guard."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_trim as backend
from trim_geometry import trimmed

class TrimDialog(W.QDialog):
    def __init__(self,ws,source=None,tool=None,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=App.ActiveDocument;self.existing=existing
        self.setObjectName('FluxTrimDialog');self.setWindowTitle(tr('面をトリム','Trim Surface'));self.resize(480,480)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.parts=[];self.loaded_stamp=None;self.validated=None
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('対象は1枚の面、切断用には面・殻全体を選びます。領域を取得し、残す領域をチェックしてプレビューします。面の自動延長は行いません。参照形状・相対配置が変わった場合は再選択します。','Select a one-face target and a whole face/shell tool. Compute regions, check the regions to keep, then Preview. No automatic surface extension. Reselect after geometry or relative-placement changes.'));note.setWordWrap(True);layout.addWidget(note)
        self.target=W.QComboBox();self.tool=W.QComboBox();form=W.QFormLayout();layout.addLayout(form);form.addRow(tr('対象','Target'),self.target);form.addRow(tr('切断面','Tool'),self.tool)
        for obj in self.doc.Objects:
            if obj==existing or not hasattr(obj,'Shape') or obj.Shape.isNull() or obj.Shape.Solids or not obj.Shape.isValid():continue
            if existing and existing in obj.OutListRecursive:continue
            if len(obj.Shape.Faces)==1 and len(obj.Shape.Edges)==len(obj.Shape.Faces[0].Edges):self.target.addItem(obj.Label,obj.Name)
            if obj.Shape.ShapeType in ('Face','Shell'):self.tool.addItem(obj.Label,obj.Name)
        if source:self.target.setCurrentIndex(self.target.findData(source.Name))
        if tool:self.tool.setCurrentIndex(self.tool.findData(tool.Name))
        self.compute_button=W.QPushButton(tr('領域を取得','Compute Regions'));layout.addWidget(self.compute_button)
        self.list=W.QListWidget();layout.addWidget(self.list,1);self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.target.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.reset));self.tool.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.reset));self.list.itemChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.compute_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.compute));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def inputs(self):return self.doc.getObject(self.target.currentData() or ''),self.doc.getObject(self.tool.currentData() or '')
    def stamp(self):
        source,tool=self.inputs();backend.checked(self.doc,source,tool,self.existing)
        return tuple((o.Name,backend.fingerprint(o),tuple(o.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.parents([o]))) for o in (source,tool)),(tuple(self.existing.getGlobalPlacement().toMatrix().A),tuple(self.existing.Keep)) if self.existing else None
    def guard(self):
        if App.ActiveDocument!=self.doc or self.loaded_stamp is None or self.stamp()!=self.loaded_stamp:raise ValueError(tr('対象が変わりました。領域を取得し直してください。','The target changed. Compute regions again.'))
    def keep(self):return [i for i in range(self.list.count()) if self.list.item(i).checkState()==QtCore.Qt.Checked]
    def invalidate(self,*args):ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def reset(self,*args):self.invalidate();self.parts=[];self.loaded_stamp=None;self.list.clear()
    def compute(self):
        self.reset()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            source,tool=self.inputs();self.parts=backend.regions(self.doc,source,tool,self.existing);self.loaded_stamp=self.stamp();keep=[]
            if self.existing and source==self.existing.Source and tool==self.existing.Tool:
                try:backend.check_reference(self.existing);keep=list(self.existing.Keep)
                except ValueError:pass
            inv=source.getGlobalPlacement().inverse()
            for i,face in enumerate(self.parts):
                c=inv.multVec(face.CenterOfMass);item=W.QListWidgetItem('%d — %.6g mm² / (%.4g, %.4g, %.4g)'%(i+1,face.Area,c.x,c.y,c.z));item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable);item.setCheckState(QtCore.Qt.Checked if i in keep else QtCore.Qt.Unchecked);self.list.addItem(item)
            self.status.setText(tr('残す領域を選択してください（少なくとも1領域を除去）。','Select regions to keep (remove at least one region).'))
        except Exception as error:self.status.setText(str(error))
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=trimmed(self.parts,self.keep())
            if self.existing:shape.Placement=self.existing.getGlobalPlacement().multiply(shape.Placement)
            ExtrudePanel.show_shape(self.host,shape,'new');target=self.existing or self.inputs()[0];self.host.hidden.append((target,bool(target.Visibility)));target.Visibility=False
            self.validated=tuple(self.keep());self.ok.setEnabled(True);self.status.setText(tr('残す面積: %.6g mm²','Retained area: %.6g mm²')%shape.Area)
        except Exception as error:self.status.setText(str(error))
    def refresh(self):
        if self.loaded_stamp is None:return
        try:self.guard()
        except Exception as error:self.reset();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated!=tuple(self.keep()):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            source,tool=self.inputs();keep=self.keep();self.invalidate();self.result_object=backend.apply(self.doc,source,tool,keep,self.existing)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx()
    if any(s.SubElementNames or s.Object.Document!=App.ActiveDocument for s in selections):raise ValueError(tr('現在の文書のオブジェクト全体を選んでください。','Select whole objects in the current document.'))
    objs=[s.Object for s in selections];existing=objs[0] if len(objs)==1 and getattr(objs[0],'FluxTrim',False) else None
    source=existing.Source if existing else objs[0] if objs else None;tool=existing.Tool if existing else objs[1] if len(objs)>1 else None
    ws.region_picker.ticket+=1;ws.region_picker.clear();return TrimDialog(ws,source,tool,existing).exec()
