import FreeCAD as App
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_cam_post as m

class PostDialog(W.QDialog):
    def __init__(self,ws,ops):
        super().__init__(ws.main);self.setWindowTitle(tr('Gコード出力','Post Process / G-code'));self.resize(850,600);self.ops=ops;self.stamp=None;form=W.QVBoxLayout(self)
        self.combo=W.QComboBox()
        for op in ops:self.combo.addItem(op.Label,op.Name)
        form.addWidget(self.combo);hint=W.QLabel(tr('LinuxCNC・ミリ・G54・絶対座標・毎分送り。面加工/矩形ポケットの単一操作。\n工具番号に対応するG43 H工具長補正を出力。円弧/穴あけ/複数操作/機械通信なし。\n出力は実機検証済みではありません。座標系と工具補正を実機側で確認してください。','LinuxCNC,mm,G54,absolute coordinates,feed per minute. One facing/rectangular pocket operation.\nOutputs G43 H tool length offset matching tool number. No arcs,drilling,multiple operations or machine connection.\nOutput is not machine validated. Check work coordinates and tool offsets on the machine.'));hint.setWordWrap(True);form.addWidget(hint)
        self.precision=W.QSpinBox();self.precision.setRange(3,6);self.precision.setValue(6);self.precision.setPrefix(tr('小数桁数: ','Decimal places: '));form.addWidget(self.precision)
        self.editor=W.QPlainTextEdit();self.editor.setReadOnly(True);form.addWidget(self.editor);self.status=W.QLabel();self.status.setWordWrap(True);form.addWidget(self.status)
        row=W.QHBoxLayout();form.addLayout(row);self.preview=W.QPushButton(tr('コード生成','Generate'));self.save_button=W.QPushButton(tr('新規ファイルへ保存…','Save New File…'));close=W.QPushButton(tr('閉じる','Close'))
        for x in (self.preview,self.save_button,close):row.addWidget(x)
        self.preview.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.generate));self.save_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.choose_save));close.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.combo.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.precision.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.timer=QtCore.QTimer(self);self.timer.setInterval(400);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start();self.invalidate()
    def invalidate(self,*args):self.stamp=None;self.editor.clear();self.save_button.setEnabled(False)
    def generate(self):
        self.invalidate()
        try:
            self.text,self.stamp=m.generate(self.ops[self.combo.currentIndex()],self.precision.value());self.editor.setPlainText(self.text);self.save_button.setEnabled(True);self.status.clear()
        except Exception as error:self.status.setText(str(error))
    def guard(self):
        if self.stamp is None:return
        try:
            if m.data(self.ops[self.combo.currentIndex()],self.precision.value())[1]!=self.stamp:raise ValueError('stale')
        except Exception:self.invalidate();self.status.setText(tr('入力が変わりました。コードを再生成してください。','Inputs changed. Generate again.'))
    def save_to(self,filename):
        self.guard()
        if self.stamp is None:raise ValueError('Generate current preview first')
        result=m.save(self.ops[self.combo.currentIndex()],self.precision.value(),filename,self.text,self.stamp);self.status.setText(tr('保存しました: ','Saved: ')+result);return result
    def choose_save(self):
        self.guard()
        if self.stamp is None:return
        filename,_=W.QFileDialog.getSaveFileName(self,tr('新規Gコードファイル','New G-code File'),'','G-code (*.ngc *.nc)',options=W.QFileDialog.DontConfirmOverwrite)
        if not filename:return
        try:self.save_to(filename)
        except Exception as error:self.status.setText(str(error))

def show(ws):
    ops=[o for o in App.ActiveDocument.Objects if any(getattr(o,n,False) for n in ('FullArcCAMPocket','FullArcCAMFacing'))] if App.ActiveDocument else []
    if not ops:raise ValueError(tr('先に面加工またはポケット加工を作成してください。','Create a facing or pocket operation first.'))
    dialog=PostDialog(ws,ops)
    try:dialog.exec_()
    finally:dialog.timer.stop();dialog.deleteLater()
