"""Distance/angle chamfer dialog with a transient, unpickable preview."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_angle_chamfer as backend


class AngleChamferDialog(W.QDialog):
    def __init__(self,ws,source,names,existing=None):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.existing=existing;self.doc=source.Document
        self.setWindowTitle(tr('距離と角度の面取り','Distance and Angle Chamfer'));self.resize(440,480)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.initial_stamp=self.stamp()
        layout=W.QVBoxLayout(self)
        label=W.QLabel(tr('対象: %s\n2つの平面に接する直線辺を面取りします。','Body: %s\nChamfers straight edges joining two planar faces.')%source.Label);label.setWordWrap(True);layout.addWidget(label)
        note=W.QLabel(tr('元のボディは保持します。作成後は結果を選択し、このコマンドで辺を再編集できます。参照形状が変わった場合は辺を選び直します。','The source body is retained. Select the result and run this command to edit its edges. Reselect edges after source geometry changes.'));note.setWordWrap(True);layout.addWidget(note)
        self.distance=W.QDoubleSpinBox();self.distance.setDecimals(8);self.distance.setRange(.001,100000);self.distance.setSuffix(' mm');self.distance.setValue(existing.Input.Distance if existing else 2);self.original_distance=existing.Input.Distance if existing else 2;self.display_distance=self.distance.value();layout.addWidget(W.QLabel(tr('距離','Distance')));layout.addWidget(self.distance)
        self.angle=W.QDoubleSpinBox();self.angle.setDecimals(8);self.angle.setRange(.1,89.9);self.angle.setSuffix('°');self.angle.setValue(existing.Input.ChamferAngle if existing else 45);self.original_angle=existing.Input.ChamferAngle if existing else 45;self.display_angle=self.angle.value();layout.addWidget(W.QLabel(tr('角度','Angle')));layout.addWidget(self.angle)
        self.reverse=W.QCheckBox(tr('距離を適用する側を反転','Flip Distance Side'));self.reverse.setChecked(bool(existing.Native.FlipDirection) if existing else False);layout.addWidget(self.reverse)
        self.faces=W.QListWidget();self.faces.setObjectName('AngleChamferEdges');layout.addWidget(self.faces,1)
        for i,edge in enumerate(source.Shape.Edges):
            name='Edge'+str(i+1);item=W.QListWidgetItem('%s — %.6g mm'%(name,edge.Length));item.setData(QtCore.Qt.UserRole,name)
            item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable);item.setCheckState(QtCore.Qt.Checked if name in names else QtCore.Qt.Unchecked);self.faces.addItem(item)
        self.status=W.QLabel(tr('プレビューで成立を確認してください。','Preview to validate the selection.'));self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.buttons.button(W.QDialogButtonBox.Cancel).setText(tr('キャンセル','Cancel'))
        self.faces.itemChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.distance.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.angle.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()

    def distance_value(self):
        return self.original_distance if self.distance.value()==self.display_distance else self.distance.value()

    def angle_value(self):
        return self.original_angle if self.angle.value()==self.display_angle else self.angle.value()

    def parameters(self):
        return (tuple(self.names()),self.distance_value(),self.angle_value(),self.reverse.isChecked(),self.initial_stamp)

    def names(self):
        return [self.faces.item(i).data(QtCore.Qt.UserRole) for i in range(self.faces.count()) if self.faces.item(i).checkState()==QtCore.Qt.Checked]

    def stamp(self):
        if self.source.Document!=self.doc or self.doc.getObject(self.source.Name)!=self.source:raise ValueError(tr('参照元がありません。','The source is missing.'))
        if self.existing and (self.existing.Document!=self.doc or self.doc.getObject(self.existing.Name)!=self.existing):raise ValueError(tr('編集対象がありません。','The edited feature is missing.'))
        return (backend.shape_fingerprint(self.source.Shape),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(self.source)),
                (tuple(self.existing.getGlobalPlacement().toMatrix().A),tuple(self.existing.Input.EdgeNames),self.existing.Input.Distance,self.existing.Input.ChamferAngle,bool(self.existing.Native.FlipDirection)) if self.existing else None)

    def guard(self):
        if App.ActiveDocument!=self.doc or self.stamp()!=self.initial_stamp:
            raise ValueError(tr('対象が変わりました。閉じて選び直してください。','The target changed. Close and reselect it.'))

    def invalidate(self,*args):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();names=self.names();shape=backend.preview(self.doc,self.source,names,self.distance_value(),self.angle_value(),self.reverse.isChecked(),self.existing)
            ExtrudePanel.show_shape(self.host,shape,'new')
            target=self.existing or self.source
            self.host.hidden.append((target,bool(target.Visibility)));target.Visibility=False
            self.validated=self.parameters();self.ok.setEnabled(True)
            self.status.setText(tr('%d辺を面取り。体積: %.6g mm³','Chamfer %d edges. Volume: %.6g mm³')%(len(names),shape.Volume))
        except Exception as error:self.status.setText(str(error))

    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated!=self.parameters():raise ValueError(tr('先にプレビューしてください。','Preview the selection first.'))
            self.invalidate();obj=backend.apply(self.doc,self.source,self.names(),self.distance_value(),self.angle_value(),self.reverse.isChecked(),self.existing)
            self.result_object=obj
            Gui.Selection.clearSelection();Gui.Selection.addSelection(obj);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

    def done(self,result):
        self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    doc=App.ActiveDocument
    if not doc or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):
        raise ValueError(tr('開いている編集を終了し、1つのボディの辺を選択してください。','Finish the current edit and select edges of one body.'))
    selections=Gui.Selection.getSelectionEx()
    if len(selections)!=1 or selections[0].Object.Document!=doc:raise ValueError(tr('1つのボディの辺を選択してください。','Select edges of one body.'))
    selection=selections[0];obj=selection.Object
    if getattr(obj,'FluxAngleChamfer',False) and not selection.SubElementNames:
        existing=obj;source=obj.Source
        names=list(obj.Input.EdgeNames)
    else:existing=None;source=obj;names=list(selection.SubElementNames)
    if not hasattr(source,'Shape') or len(source.Shape.Solids)!=1:raise ValueError(tr('単一ソリッドを選択してください。','Select one solid.'))
    ws.region_picker.clear()
    dialog=AngleChamferDialog(ws,source,names,existing)
    return dialog.exec()
