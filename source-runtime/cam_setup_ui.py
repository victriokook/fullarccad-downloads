import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_cam_setup as m

class SetupDialog(W.QDialog):
    def __init__(self,ws,source):
        self.stamp=m.signature(source);super().__init__(ws.main);self.source=source;self.setWindowTitle(tr('加工セットアップ','Machining Setup'));self.setObjectName('FullArcCAMSetup');form=W.QFormLayout(self)
        hint=W.QLabel(tr('現在の形状の独立コピーからnative CAMジョブを作成します。原本変更には追従しません。\n座標系は現在の世界XYZ。素材は全方向同じ余裕の直方体、工具はエンドミル1本。\nここでは工具経路・機械送信は実行しません。','Create a native CAM job from an independent copy; source changes do not update it.\nCurrent world XYZ, bounding-box stock with equal margins, one endmill.\nThis dialog creates no toolpath and sends nothing to a machine.'));hint.setWordWrap(True);form.addRow(hint);self.fields={}
        for key,ja,en,lo,hi,default in [('margin','素材余裕 mm','Stock Margin mm',0,1000,1),('diameter','工具径 mm','Tool Diameter mm',.01,1000,5),('feed','送り mm/min','Feed mm/min',.01,100000,300),('plunge','切込み送り mm/min','Plunge mm/min',.01,100000,100),('rpm','主軸 rpm','Spindle rpm',1,100000,3000)]:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(lo,hi);spin.setValue(default);self.fields[key]=spin;form.addRow(tr(ja,en),spin)
        self.number=W.QSpinBox();self.number.setRange(1,999);form.addRow(tr('工具番号','Tool Number'),self.number);self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons);self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start()
    def guard(self):
        try:
            if m.signature(self.source)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('原本が変わりました。開き直してください。','Source changed. Reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.create(self.source,expected=self.stamp,tool_number=self.number.value(),**{k:v.value() for k,v in self.fields.items()})
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws):
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('ソリッド全体を1つ選択してください。','Select one whole solid.'))
    dialog=SetupDialog(ws,selected[0].Object)
    try:dialog.exec_()
    finally:dialog.timer.stop();dialog.deleteLater()
