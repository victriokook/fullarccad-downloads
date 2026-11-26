"""Whole-curve projection dialog; explicit all-intersections output."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
from model_defeature import fingerprint
import model_projection as backend
from single_face_ui import is_single_face

class ProjectionDialog(W.QDialog):
    def __init__(self,ws,source=None,target=None,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=App.ActiveDocument;self.existing=existing
        self.setObjectName('FluxProjectionDialog');self.setWindowTitle(tr('曲面へ投影','Project to Surface'))
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('線・ワイヤ全体を1枚の面へ平行投影します。表裏すべての交差線を保持します。方向は入力線のローカル座標です。最近点への投影ではありません。','Parallel-project a whole edge/wire onto one finite face. Retains ALL intersections, including front/back branches. Direction uses the input curve local coordinates. Not closest-point projection.'));note.setWordWrap(True);layout.addWidget(note)
        form=W.QFormLayout();layout.addLayout(form);self.source=W.QComboBox();self.target=W.QComboBox()
        form.addRow(tr('入力線','Input Curve'),self.source);form.addRow(tr('対象面','Target Face'),self.target)
        for obj in self.doc.Objects:
            if obj==existing or not hasattr(obj,'Shape') or obj.Shape.isNull():continue
            if existing and existing in obj.OutListRecursive:continue
            if obj.Shape.ShapeType in ('Edge','Wire'):self.source.addItem(obj.Label,obj.Name)
            if is_single_face(obj.Shape):self.target.addItem(obj.Label,obj.Name)
        if source:self.source.setCurrentIndex(self.source.findData(source.Name))
        if target:self.target.setCurrentIndex(self.target.findData(target.Name))
        self.axes=[];initial=existing.Direction if existing else App.Vector(0,0,-1)
        for label,value in zip(('X','Y','Z'),(initial.x,initial.y,initial.z)):
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(-1e6,1e6);spin.setValue(value);self.axes.append(spin);form.addRow(label,spin);spin.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.source.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.target.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def inputs(self):return self.doc.getObject(self.source.currentData() or ''),self.doc.getObject(self.target.currentData() or '')
    def vector(self):return tuple(v.value() for v in self.axes)
    def stamp(self):
        source,target=self.inputs();backend.checked(self.doc,source,target,self.existing)
        return tuple((o.Name,fingerprint(o),tuple(o.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.parents([o]))) for o in (source,target)),self.vector(),(self.existing.Source.Name if self.existing.Source else None,self.existing.Target.Name if self.existing.Target else None,tuple(self.existing.Direction),self.existing.Error,fingerprint(self.existing),tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
    def invalidate(self,*args):ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def guard(self):
        if App.ActiveDocument!=self.doc or self.validated is None or self.stamp()!=self.validated:raise ValueError(tr('対象が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            source,target=self.inputs();shape=backend.preview(self.doc,source,target,self.vector(),self.existing);self.validated=self.stamp();ExtrudePanel.show_shape(self.host,shape,'new');self.ok.setEnabled(True);self.status.setText(tr('全%d辺を保持します。','Retain all %d edges.')%len(shape.Edges))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def refresh(self):
        if self.validated is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard();source,target=self.inputs();vector=self.vector();self.invalidate();self.result_object=backend.apply(self.doc,source,target,vector,self.existing)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx();existing=None;source=target=None
    if any(s.SubElementNames for s in selections):raise ValueError(tr('オブジェクト全体を選択してください。','Select whole objects.'))
    objects=[s.Object for s in selections]
    if len(objects)==1 and getattr(objects[0],'FluxProjection',False):existing=objects[0];source=existing.Source;target=existing.Target
    else:
        if len(objects) not in (0,2):raise ValueError(tr('線と面を1つずつ、または何も選ばず起動してください。','Select one curve and one face, or start with no selection.'))
        if objects and (sum(o.Shape.ShapeType in ('Edge','Wire') for o in objects if hasattr(o,'Shape'))!=1 or sum(is_single_face(o.Shape) for o in objects if hasattr(o,'Shape'))!=1):raise ValueError(tr('線と面を1つずつ選択してください。','Select exactly one curve and one face.'))
        for obj in objects:
            if hasattr(obj,'Shape') and obj.Shape.ShapeType in ('Edge','Wire'):source=obj
            elif hasattr(obj,'Shape') and is_single_face(obj.Shape):target=obj
    ws.region_picker.ticket+=1;ws.region_picker.clear()
    return ProjectionDialog(ws,source,target,existing).exec()
