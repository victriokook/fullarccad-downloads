import FreeCAD as App
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_cam_profile as m

class ProfileDialog(W.QDialog):
    def __init__(self,ws,jobs):
        super().__init__(ws.main);self.setWindowTitle(tr('2D輪郭加工','2D Contour'));form=W.QFormLayout(self);self.jobs=jobs;self.combo=W.QComboBox()
        for job in jobs:self.combo.addItem(job.Label,job.Name)
        form.addRow(tr('加工セットアップ','Machining Setup'),self.combo);hint=W.QLabel(tr('直線輪郭・一定断面のZ方向ソリッド外周をnative Profileで加工。穴なし・外側補正・時計回り。\n深さは世界Z値。衝突判定・取付具・タブ・機械通信なし。','Native Profile for a straight-polygon vertical constant-section solid exterior. No holes;outside compensation,clockwise.\nDepths are world Z. No collision checking,fixtures,tabs or machine connection.'));hint.setWordWrap(True);form.addRow(hint);self.fields={}
        for key,ja,en in [('start','開始Z','Start Z'),('final','終了Z','Final Z'),('step','切込み量','Step Down'),('safe','安全Z','Safe Z'),('clearance','退避Z','Clearance Z')]:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(-1e6,1e6);self.fields[key]=spin;form.addRow(tr(ja,en)+' mm',spin)
        self.status=W.QLabel();form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);form.addRow(buttons);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.combo.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.load));self.load();self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start()
    def load(self):
        try:
            self.job=self.jobs[self.combo.currentIndex()];self.stamp=m.signature(self.job)
            for k,v in m.defaults(self.job).items():self.fields[k].setValue(v);self.fields[k]._baseline=(self.fields[k].value(),v)
            self.ok.setEnabled(True);self.status.clear()
        except Exception as error:self.ok.setEnabled(False);self.status.setText(str(error))
    def guard(self):
        try:
            if m.signature(self.job)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('セットアップが変わりました。開き直してください。','Setup changed. Reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.create(self.job,expected=self.stamp,**{k:(s._baseline[1] if s.value()==s._baseline[0] else s.value()) for k,s in self.fields.items()})
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    jobs=[o for o in App.ActiveDocument.Objects if getattr(o,'FullArcCAMSetup',False)] if App.ActiveDocument else []
    if not jobs:raise ValueError(tr('先に加工セットアップを作成してください。','Create a machining setup first.'))
    dialog=ProfileDialog(ws,jobs)
    try:dialog.exec_()
    finally:dialog.timer.stop();dialog.deleteLater()
