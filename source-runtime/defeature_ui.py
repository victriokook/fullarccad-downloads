"""Face removal dialog with a transient, unpickable preview."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
import model_defeature as backend


class DefeatureDialog(W.QDialog):
    def __init__(self,ws,source,names,existing=None):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.existing=existing;self.doc=source.Document
        self.setWindowTitle(tr('面を削除して埋める','Delete Faces and Heal'));self.resize(440,480)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.initial_stamp=self.stamp()
        layout=W.QVBoxLayout(self)
        label=W.QLabel(tr('対象: %s\n穴や突起を構成する面をすべて指定します。','Body: %s\nSelect all faces belonging to the hole or protrusion.')%source.Label);label.setWordWrap(True);layout.addWidget(label)
        note=W.QLabel(tr('元のボディは保持します。作成後は結果を選択し、このコマンドで面を再編集できます。参照形状が変わった場合は面を選び直します。','The source body is retained. Select the result and run this command to edit its faces. Reselect faces after source geometry changes.'));note.setWordWrap(True);layout.addWidget(note)
        self.faces=W.QListWidget();self.faces.setObjectName('DefeatureFaces');layout.addWidget(self.faces,1)
        for i,face in enumerate(source.Shape.Faces):
            name='Face'+str(i+1);item=W.QListWidgetItem('%s — %.6g mm²'%(name,face.Area));item.setData(QtCore.Qt.UserRole,name)
            item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable);item.setCheckState(QtCore.Qt.Checked if name in names else QtCore.Qt.Unchecked);self.faces.addItem(item)
        self.status=W.QLabel(tr('プレビューで成立を確認してください。','Preview to validate the selection.'));self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.buttons.button(W.QDialogButtonBox.Cancel).setText(tr('キャンセル','Cancel'))
        self.faces.itemChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()

    def names(self):
        return [self.faces.item(i).data(QtCore.Qt.UserRole) for i in range(self.faces.count()) if self.faces.item(i).checkState()==QtCore.Qt.Checked]

    def stamp(self):
        if self.source.Document!=self.doc or self.doc.getObject(self.source.Name)!=self.source:raise ValueError(tr('参照元がありません。','The source is missing.'))
        if self.existing and (self.existing.Document!=self.doc or self.doc.getObject(self.existing.Name)!=self.existing):raise ValueError(tr('編集対象がありません。','The edited feature is missing.'))
        return (backend.fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),
                (tuple(self.existing.getGlobalPlacement().toMatrix().A),tuple(self.existing.FaceNames),self.existing.SourceFingerprint) if self.existing else None)

    def guard(self):
        if App.ActiveDocument!=self.doc or self.stamp()!=self.initial_stamp:
            raise ValueError(tr('対象が変わりました。閉じて選び直してください。','The target changed. Close and reselect it.'))

    def invalidate(self,*args):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();names=self.names();shape=backend.preview(self.source,names,self.existing)
            ExtrudePanel.show_shape(self.host,shape,'new')
            target=self.existing or self.source
            self.host.hidden.append((target,bool(target.Visibility)));target.Visibility=False
            self.validated=(tuple(names),self.initial_stamp);self.ok.setEnabled(True)
            self.status.setText(tr('%d面を除去して埋め直します。結果の体積: %.6g mm³','Remove and heal %d faces. Result volume: %.6g mm³')%(len(names),shape.Volume))
        except Exception as error:self.status.setText(str(error))

    def refresh(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated!=(tuple(self.names()),self.initial_stamp):raise ValueError(tr('先にプレビューしてください。','Preview the selection first.'))
            self.invalidate();obj=backend.apply(self.doc,self.source,self.names(),self.existing)
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
    if getattr(obj,'FluxDefeature',False) and not selection.SubElementNames:
        existing=obj;source=obj.Source
        names=list(obj.FaceNames) if backend.fingerprint(source)==obj.SourceFingerprint and backend.containers(source)==list(obj.SourceContainers) else []
    else:existing=None;source=obj;names=list(selection.SubElementNames)
    backend.solid(source)
    if names:backend.face_indices(names,len(source.Shape.Faces))
    ws.region_picker.clear()
    dialog=DefeatureDialog(ws,source,names,existing)
    return dialog.exec()
