import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_assembly as assembly,motion_link as m
class MotionDialog(W.QDialog):
    def __init__(self,ws,driver,follower,existing=None):
        self.stamp=m.stamp(driver,follower,existing);super().__init__(ws.main);self.ws=ws;self.driver=driver;self.follower=follower;self.existing=existing;self.setWindowTitle(tr('回転比のモーションリンク','Rotational Motion Link'));self.setObjectName('FullArcMotionLink')
        form=W.QFormLayout(self);hint=W.QLabel(tr('独立した回転ジョイント2つを1方向に連動。作成時の角度を基準に比率を適用。\n各角度±360°、比率.001～1000。連鎖・双方向ソルバー・歯形接触・形状プレビューなし。','Link two independent revolute joints one way,relative to their angles at creation.\nAngles±360degrees,ratio.001–1000. No chains,bidirectional solver,gear contact or geometry preview.'));hint.setWordWrap(True);form.addRow(hint)
        form.addRow(tr('駆動 → 従動','Driver → Driven'),W.QLabel(driver.Label+' → '+follower.Label));values=m.settings(existing) if existing else dict(one=360.,two=360.,reverse=False);self.fields={}
        for key,ja,en in [('one','駆動側の回転角 °','Driver Rotation degrees'),('two','従動側の回転角 °','Driven Rotation degrees')]:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(.001,360);spin.setValue(values[key]);spin._baseline=(spin.value(),values[key]);self.fields[key]=spin;form.addRow(tr(ja,en),spin)
        self.reverse=W.QCheckBox(tr('回転方向を反転','Reverse direction'));self.reverse.setChecked(values['reverse']);form.addRow(self.reverse)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        if existing:
            self.release_button=W.QPushButton(tr('リンクを解除（姿勢保持）','Release Link (keep pose)'));self.release_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.release));form.addRow(self.release_button)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start()
    def inputs(self):return dict({k:s._baseline[1] if s.value()==s._baseline[0] else s.value() for k,s in self.fields.items()},reverse=self.reverse.isChecked())
    def guard(self):
        try:
            if m.stamp(self.driver,self.follower,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:
            self.ok.setEnabled(False)
            if self.existing:self.release_button.setEnabled(False)
            self.status.setText(tr('参照・角度・設定が変わりました。開き直してください。','Inputs,angles or settings changed. Reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.driver,self.follower,existing=self.existing,expected=self.stamp,**self.inputs())
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def release(self):
        self.guard()
        if not self.release_button.isEnabled():return
        try:m.release(self.existing)
        except Exception as error:self.status.setText(str(error));return
        super().accept()
def show(ws):
    if App.ActiveDocument is None or ws.current_sketch() or Gui.Control.activeDialog():raise ValueError('Open a document and finish editing')
    selected=Gui.Selection.getSelectionEx();existing=None
    if any(s.SubElementNames for s in selected):raise ValueError('Select whole joints or one motion link')
    objects=[s.Object.Driver if getattr(s.Object,'FluxComponent',False) and s.Object.Driver else s.Object for s in selected]
    if not objects:
        joints=[j for j in assembly.joints(App.ActiveDocument) if str(j.Kind)=='revolute' and not j.getParentGeoFeatureGroup()]
        if len(joints)<2:raise ValueError(tr('回転ジョイントを2つ作成してください。','Create two revolute joints first.'))
        labels=[j.Label+' ['+j.Name+']' for j in joints]
        first,ok=W.QInputDialog.getItem(ws.main,tr('回転比リンク','Motion Link'),tr('駆動ジョイント','Driving Joint'),labels,0,False)
        if not ok:return
        driver=joints[labels.index(first)];remaining=[j for j in joints if j!=driver];labels=[j.Label+' ['+j.Name+']' for j in remaining]
        second,ok=W.QInputDialog.getItem(ws.main,tr('回転比リンク','Motion Link'),tr('従動ジョイント','Driven Joint'),labels,0,False)
        if not ok:return
        objects=[driver,remaining[labels.index(second)]]
    if len(objects)==1 and getattr(objects[0],'FluxJoint',False):
        matches=[link for link in m.links(App.ActiveDocument) if link.Driver==objects[0] or link.DrivenName==objects[0].Name]
        if len(matches)==1:objects=matches
    if len(objects)==1 and getattr(objects[0],'FluxMotionLink',False):existing=objects[0];driver=existing.Driver;follower=m.driven(existing)
    elif len(objects)==2:
        driver,follower=objects
        existing=next((link for link in m.links(App.ActiveDocument) if link.Driver==driver and link.DrivenName==follower.Name),None)
    else:raise ValueError(tr('駆動・従動の回転ジョイントを順に選ぶか、既存リンクを選択してください。','Select driver then driven revolute joint,or one existing link.'))
    dialog=MotionDialog(ws,driver,follower,existing)
    try:dialog.exec_()
    finally:dialog.timer.stop();dialog.deleteLater()
