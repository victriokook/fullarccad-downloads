"""Face removal dialog with a transient, unpickable preview."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_solid_draft as backend


class SolidDraftDialog(W.QDialog):
    def __init__(self,ws,source,names,existing=None):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.existing=existing;self.doc=source.Document
        self.setWindowTitle(tr('抜き勾配','Solid Face Draft'));self.resize(440,480)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.initial_stamp=self.stamp()
        layout=W.QVBoxLayout(self)
        label=W.QLabel(tr('対象: %s\n中立面に垂直な平面、または軸が中立面の法線と平行な円柱面・完全な円すい台側面を加工します。','Body: %s\nDraft perpendicular planar sides, or complete cylindrical/conical frustum sides with their axis parallel to the neutral-plane normal.')%source.Label);label.setWordWrap(True);layout.addWidget(label)
        note=W.QLabel(tr('元のボディは保持します。作成後は結果を選択し、このコマンドで面を再編集できます。参照形状が変わった場合は面を選び直します。円柱・円すい台は半径変化が元の最小半径未満となる範囲に限定します。円すい台の角度は元の角度への加算ではなく、抜き方向に対する目標角度です。円すい頂点・部分扇形は対象外です。','The source body is retained. Select the result and run this command to edit its faces. Reselect faces after source geometry changes. Cylinder/cone radius change must remain smaller than the original minimum radius in either direction. For a cone the angle is the target angle to the pull direction, rather than an increment. Cone apices and partial sectors are excluded.'));note.setWordWrap(True);layout.addWidget(note)
        self.neutral=W.QComboBox();layout.addWidget(W.QLabel(tr('中立面','Neutral plane')));layout.addWidget(self.neutral)
        for i in range(len(source.Shape.Faces)):self.neutral.addItem('Face'+str(i+1))
        self.neutral.setCurrentText(existing.Input.NeutralName if existing else 'Face1')
        self.angle=W.QDoubleSpinBox();self.angle.setDecimals(8);self.angle.setRange(.00000001,45);self.angle.setSuffix('°');self.angle.setValue(existing.Input.DraftAngle if existing else 5);self.original_angle=existing.Input.DraftAngle if existing else 5;self.display_angle=self.angle.value();layout.addWidget(W.QLabel(tr('角度','Angle')));layout.addWidget(self.angle)
        self.reverse=W.QCheckBox(tr('反転','Reverse'));self.reverse.setChecked(bool(existing.Native.Reversed) if existing else False);layout.addWidget(self.reverse)
        self.faces=W.QListWidget();self.faces.setObjectName('SolidDraftFaces');layout.addWidget(self.faces,1)
        for i,face in enumerate(source.Shape.Faces):
            name='Face'+str(i+1);item=W.QListWidgetItem('%s — %.6g mm²'%(name,face.Area));item.setData(QtCore.Qt.UserRole,name)
            item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable);item.setCheckState(QtCore.Qt.Checked if name in names else QtCore.Qt.Unchecked);self.faces.addItem(item)
        self.status=W.QLabel(tr('プレビューで成立を確認してください。','Preview to validate the selection.'));self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.buttons.button(W.QDialogButtonBox.Cancel).setText(tr('キャンセル','Cancel'))
        self.faces.itemChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.neutral.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.angle.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()

    def angle_value(self):
        return self.original_angle if self.angle.value()==self.display_angle else self.angle.value()

    def parameters(self):
        return (tuple(self.names()),self.neutral.currentText(),self.angle_value(),self.reverse.isChecked(),self.initial_stamp)

    def names(self):
        return [self.faces.item(i).data(QtCore.Qt.UserRole) for i in range(self.faces.count()) if self.faces.item(i).checkState()==QtCore.Qt.Checked]

    def stamp(self):
        if self.source.Document!=self.doc or self.doc.getObject(self.source.Name)!=self.source:raise ValueError(tr('参照元がありません。','The source is missing.'))
        if self.existing and (self.existing.Document!=self.doc or self.doc.getObject(self.existing.Name)!=self.existing):raise ValueError(tr('編集対象がありません。','The edited feature is missing.'))
        return (backend.shape_fingerprint(self.source.Shape),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(self.source)),
                (tuple(self.existing.getGlobalPlacement().toMatrix().A),tuple(self.existing.Input.FaceNames),self.existing.Input.NeutralName,self.existing.Input.DraftAngle,bool(self.existing.Native.Reversed)) if self.existing else None)

    def guard(self):
        if App.ActiveDocument!=self.doc or self.stamp()!=self.initial_stamp:
            raise ValueError(tr('対象が変わりました。閉じて選び直してください。','The target changed. Close and reselect it.'))

    def invalidate(self,*args):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();names=self.names();shape=backend.preview(self.doc,self.source,names,self.neutral.currentText(),self.angle_value(),self.reverse.isChecked(),self.existing)
            ExtrudePanel.show_shape(self.host,shape,'new')
            target=self.existing or self.source
            self.host.hidden.append((target,bool(target.Visibility)));target.Visibility=False
            self.validated=self.parameters();self.ok.setEnabled(True)
            self.status.setText(tr('%d面に抜き勾配。体積: %.6g mm³','Draft %d faces. Volume: %.6g mm³')%(len(names),shape.Volume))
        except Exception as error:self.status.setText(str(error))

    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated!=self.parameters():raise ValueError(tr('先にプレビューしてください。','Preview the selection first.'))
            self.invalidate();obj=backend.apply(self.doc,self.source,self.names(),self.neutral.currentText(),self.angle_value(),self.reverse.isChecked(),self.existing)
            self.result_object=obj
            Gui.Selection.clearSelection();Gui.Selection.addSelection(obj);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

    def done(self,result):
        self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    doc=App.ActiveDocument
    if not doc or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):
        raise ValueError(tr('開いている編集を終了し、1つのボディの面を選択してください。','Finish the current edit and select faces of one body.'))
    selections=Gui.Selection.getSelectionEx()
    if len(selections)!=1 or selections[0].Object.Document!=doc:raise ValueError(tr('1つのボディの面を選択してください。','Select faces of one body.'))
    selection=selections[0];obj=selection.Object
    if getattr(obj,'FluxSolidDraft',False) and not selection.SubElementNames:
        existing=obj;source=obj.Source
        names=list(obj.Input.FaceNames)
    else:existing=None;source=obj;names=list(selection.SubElementNames)
    if not hasattr(source,'Shape') or len(source.Shape.Solids)!=1:raise ValueError(tr('単一ソリッドを選択してください。','Select one solid.'))
    ws.region_picker.clear()
    dialog=SolidDraftDialog(ws,source,names,existing)
    return dialog.exec()
