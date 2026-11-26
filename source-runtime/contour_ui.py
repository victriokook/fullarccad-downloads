"""Create a new sheet from one open straight sketch contour."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_contour as m
class ContourDialog(W.QDialog):
    def __init__(self,ws,source,existing=None):
        stamp=m.signature(source,existing)
        super().__init__(ws.main);self.setObjectName('FullArcContour');self.setWindowTitle(tr('輪郭フランジ','Contour Flange'));self.source=source;self.existing=existing;self.stamp=stamp
        vals=m.settings(existing) if existing else dict(thickness=1.,length=20.,radius=1.,side='Inside',midplane=False,reverse=False)
        form=W.QFormLayout(self);hint=W.QLabel(tr('開いたスケッチの直線1～50本から新しい板金ボディを作成します。内角10～170°。\n円弧・スプライン・既存板への結合・複数輪郭・製造認証・対話形状プレビューはありません。',
        'Create a new sheet body from1..50 straight segments in one open sketch. Internal angles10..170degrees.\nNo arcs,splines,joining existing sheets,multiple contours,manufacturing certification or interactive shape preview.'));hint.setWordWrap(True);form.addRow(hint);form.addRow(tr('スケッチ','Sketch'),W.QLabel(source.Label))
        self.fields={}
        for key,label,upper in [('thickness',tr('板厚','Thickness'),1000),('length',tr('押出長さ','Extrusion Length'),100000),('radius',tr('内側曲げ半径','Inner Bend Radius'),100000)]:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(.001,upper);spin.setSuffix(' mm');spin.setValue(vals[key]);spin._baseline=(spin.value(),vals[key]);self.fields[key]=spin;form.addRow(label,spin)
        self.side=W.QComboBox()
        for label,key in [(tr('内側','Inside'),'Inside'),(tr('外側','Outside'),'Outside'),(tr('中央','Middle'),'Middle')]:self.side.addItem(label,key)
        self.side.setCurrentIndex(self.side.findData(vals['side']));form.addRow(tr('板の配置（native基準）','Material Side (native)'),self.side)
        self.midplane=W.QCheckBox(tr('対称押出','Symmetric Extrusion'));self.midplane.setChecked(vals['midplane']);form.addRow(self.midplane)
        self.reverse=W.QCheckBox(tr('押出方向反転（非対称時）','Reverse Extrusion (one-sided)'));self.reverse.setChecked(vals['reverse']);form.addRow(self.reverse)
        self.midplane.toggled.connect(__import__('builtins')._fullarc_qt_slot(lambda enabled:self.reverse.setEnabled(not enabled),(1, 1, False, False)));self.reverse.setEnabled(not self.midplane.isChecked())
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start();self.resize(630,360)
    def inputs(self):
        vals={k:(s._baseline[1] if s.value()==s._baseline[0] else s.value()) for k,s in self.fields.items()};vals.update(side=self.side.currentData(),midplane=self.midplane.isChecked(),reverse=self.reverse.isChecked());return vals
    def guard(self):
        try:
            if m.signature(self.source,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('参照・形状・設定が変わりました。閉じて開き直してください。','Inputs,geometry or settings changed. Close and reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.source,existing=self.existing,expected=self.stamp,**self.inputs())
        except Exception as error:self.status.setText(str(error));return
        super().accept()
def show(ws,existing=None):
    if App.ActiveDocument is None or ws.current_sketch() or Gui.Control.activeDialog():raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active operation.'))
    if existing is None:
        sel=Gui.Selection.getSelectionEx()
        if len(sel)!=1 or sel[0].SubElementNames:raise ValueError(tr('開いたスケッチ全体、または輪郭フランジ全体を選択してください。','Select a whole open sketch or contour flange.'))
        obj=sel[0].Object
        if getattr(obj,'FluxContour',False):existing=obj
        else:source=obj
    if existing is not None:source=existing.Source
    dialog=ContourDialog(ws,source,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:ws.compact();return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
