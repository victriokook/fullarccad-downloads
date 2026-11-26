import FreeCAD as App
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_cam_face as m

class FaceDialog(W.QDialog):
    def __init__(self,ws,jobs):
        super().__init__(ws.main);self.setObjectName('FullArcFacing');self.setWindowTitle(tr('面加工','Facing'));self.jobs=jobs;form=W.QFormLayout(self)
        self.combo=W.QComboBox()
        for job in jobs:self.combo.addItem(job.Label,job.Name)
        form.addRow(tr('加工セットアップ','Machining Setup'),self.combo);self.faces=W.QComboBox();form.addRow(tr('加工する上面','Top Face'),self.faces)
        hint=W.QLabel(tr('世界XYに沿う穴なし矩形上面1つ。X方向の往復経路。\n対象は選択面の範囲で、素材全体ではありません。終了Zはモデル上面以上。横送り5～80%（整数）。\n衝突検査・機械通信なし。','One hole-free rectangular top face aligned with world XY;X-direction zigzag.\nCovers the selected face,not the entire stock. Final Z at or above model top;integer5..80% stepover.\nNo collision checking or machine connection.'));hint.setWordWrap(True);form.addRow(hint)
        self.fields={}
        for key,ja,en,lo,hi in [('start','開始Z mm','Start Z mm',-1e6,1e6),('final','終了Z mm','Final Z mm',-1e6,1e6),('step','切込み mm','Step Down mm',.001,1e6),('safe','安全Z mm','Safe Z mm',-1e6,1e6),('clearance','退避Z mm','Clearance Z mm',-1e6,1e6),('stepover','横送り %','Stepover %',5,80)]:
            spin=W.QDoubleSpinBox();spin.setDecimals(0 if key=='stepover' else 8);spin.setRange(lo,hi);self.fields[key]=spin;form.addRow(tr(ja,en),spin)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);form.addRow(buttons);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.combo.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.load_job));self.faces.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.load_face));self.load_job();self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start()
    def load_job(self):
        self.stamp=None;self.ok.setEnabled(False);self.faces.blockSignals(True);self.faces.clear()
        try:
            self.job=self.jobs[self.combo.currentIndex()]
            for index in m.candidates(self.job):
                bb=self.job.Model.Group[0].Shape.Faces[index-1].BoundBox
                self.faces.addItem('Face'+str(index)+'  '+format(bb.XLength,'.6g')+' × '+format(bb.YLength,'.6g')+' mm  Z='+format(bb.ZMin,'.6g'),index)
        except Exception as error:self.status.setText(str(error))
        finally:self.faces.blockSignals(False)
        self.load_face()
    def load_face(self):
        self.stamp=None;self.ok.setEnabled(False)
        if self.faces.currentIndex()<0:
            self.status.setText(tr('対応する矩形加工する上面がありません。','No supported rectangular top face.'));return
        try:
            self.face_index=int(self.faces.currentData());self.stamp=m.signature(self.job,self.face_index)
            for key,value in m.defaults(self.job,self.face_index).items():self.fields[key].setValue(value);self.fields[key]._baseline=(self.fields[key].value(),value)
            self.ok.setEnabled(True);self.status.clear()
        except Exception as error:self.status.setText(str(error))
    def guard(self):
        if self.stamp is None:return
        try:
            if m.signature(self.job,self.face_index)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('原本または工具が変わりました。開き直してください。','Model or tool changed. Reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.create(self.job,self.face_index,expected=self.stamp,**{k:(s._baseline[1] if s.value()==s._baseline[0] else s.value()) for k,s in self.fields.items()})
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    jobs=[o for o in App.ActiveDocument.Objects if getattr(o,'FullArcCAMSetup',False)] if App.ActiveDocument else []
    if not jobs:raise ValueError(tr('先に加工セットアップを作成してください。','Create a machining setup first.'))
    dialog=FaceDialog(ws,jobs)
    try:dialog.exec_()
    finally:dialog.timer.stop();dialog.deleteLater()
