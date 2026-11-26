"""Whole-object guide sweep dialog; native orientation-only auxiliary spine."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_guided_sweep as m

class GuidedDialog(W.QDialog):
    def __init__(self,ws,profile,path,rail,existing=None):
        self.stamp=m.signature(profile,path,rail,existing)
        super().__init__(ws.main);self.setObjectName('FullArcGuidedSweep');self.setWindowTitle(tr('ガイドレール付きスイープ','Sweep with Guide Rail'))
        self.ws=ws;self.sources=(profile,path,rail);self.existing=existing
        form=W.QFormLayout(self)
        hint=W.QLabel(tr('選択順: 閉じた平面断面 → 経路 → ガイドレール。\n断面の尺度なし・姿勢制御のみ。経路／レールは順方向の単一開辺。\nガイド始点は断面境界上、経路始点は断面内。尺度変更・ストレッチ・複数辺・形状プレビューなし。',
        'Selection order: closed planar profile, path, guide rail.\nOrientation only, no profile scaling. Path/rail: one forward open edge.\nGuide starts on profile boundary; path starts inside profile. No scaling, stretch, chains or geometry preview.'))
        hint.setWordWrap(True);form.addRow(hint)
        for label,s in zip((tr('断面','Profile'),tr('経路','Path'),tr('ガイドレール','Guide Rail')),self.sources):form.addRow(label,W.QLabel(s.Label))
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start();self.resize(620,300)
    def guard(self):
        try:
            if m.signature(*self.sources,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('参照・形状が変わりました。閉じて再選択してください。','Inputs or geometry changed. Close and reselect.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(*self.sources,existing=self.existing,expected=self.stamp)
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws,existing=None):
    if App.ActiveDocument is None or ws.current_sketch() or Gui.Control.activeDialog():raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active operation.'))
    selected=Gui.Selection.getSelectionEx()
    if existing is None and len(selected)==1 and not selected[0].SubElementNames and getattr(selected[0].Object,'FluxGuidedSweep',False):existing=selected[0].Object
    if existing is not None:
        if not getattr(existing,'FluxGuidedSweep',False):raise ValueError('Select a guided sweep')
        sources=(existing.Profile,existing.Path,existing.GuideRail)
    else:
        if len(selected)!=3 or any(s.SubElementNames for s in selected):raise ValueError(tr('断面・経路・レールの3オブジェクト全体を順番に選択してください。','Select three whole objects in order: profile,path,guide rail.'))
        sources=tuple(s.Object for s in selected)
    dialog=GuidedDialog(ws,*sources,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:ws.compact();return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
