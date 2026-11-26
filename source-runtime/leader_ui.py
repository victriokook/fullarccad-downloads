"""Manual plain-text notes with a three-point native leader."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import drawing,model_leader as m


class LeaderDialog(W.QDialog):
    def __init__(self,ws,view,existing=None):
        stamp=m.signature(view,existing);text,points,center=m.settings(existing) if existing else ('',((0.,0.),(15.,15.),(30.,15.)),(50.,15.))
        super().__init__(ws.main);self.setObjectName('FullArcLeaderNote');self.setWindowTitle(tr('引出線付き注記','Leader Note'))
        self.view=view;self.existing=existing;self.stamp=stamp;form=W.QFormLayout(self)
        hint=W.QLabel(tr('用紙上のmmでビュー中心から指定します。ビュー移動に追従し、尺度変更では線や文字を伸縮しません。\n3点折線と文章中心を指定。文章幅40mm、標準書式。辺への関連付け・スナップ・穴ねじ自動注記はありません。',
                        'Printed mm relative to the view center. Follows view movement;lines and text do not scale with the model.\nSpecify three line points and the text center.40mm text width,native default formatting. No edge attachment,snaps or automatic hole/thread notes.'))
        hint.setWordWrap(True);form.addRow(hint)
        self.text=W.QPlainTextEdit(text);self.text.setObjectName('leaderText');form.addRow(tr('文章（最大1000文字・20行）','Text (up to1000 characters,20 lines)'),self.text)
        self.fields=[]
        labels=[tr('矢印先端','Arrow Tip'),tr('折曲点','Bend'),tr('引出線終端','Leader End'),tr('注記中心','Text Center')]
        for name,xy in zip(labels,list(points)+[center]):
            for axis,value in zip('XY',xy):
                spin=W.QDoubleSpinBox();spin.setRange(-1e6,1e6);spin.setDecimals(8);spin.setSuffix(' mm');spin.setValue(value);spin._baseline=(spin.value(),value);self.fields.append(spin);form.addRow(name+' '+axis,spin)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok)
        buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start();self.resize(700,650)

    def inputs(self):
        coords=[s._baseline[1] if s.value()==s._baseline[0] else s.value() for s in self.fields]
        return self.text.toPlainText(),tuple(tuple(coords[i:i+2]) for i in (0,2,4)),tuple(coords[6:8])

    def refresh_guard(self):
        try:
            if m.signature(self.view,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:
            self.ok.setEnabled(False);self.status.setText(tr('参照ビュー・形状・注記が変わりました。閉じて開き直してください。','The view,geometry or note changed. Close and reopen.'))

    def accept(self):
        self.refresh_guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.view,*self.inputs(),existing=self.existing,expected=self.stamp)
        except Exception as error:self.status.setText(str(error));return
        super().accept()


def show(ws,existing=None):
    drawing.ready(ws)
    if existing is None:
        selected=Gui.Selection.getSelectionEx()
        if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('単独投影図全体、または引出線付き注記を選択してください。','Select a whole base view or leader note.'))
        obj=selected[0].Object
        if getattr(obj,'FluxLeaderNote',False) or getattr(obj,'FluxLeaderLine',False):existing=obj
        else:view=obj
    if existing is not None:view=m.pair(existing)[0].LeaderParent
    page=m.model_balloon.target(view);dialog=LeaderDialog(ws,view,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:drawing.show(ws,page);return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
