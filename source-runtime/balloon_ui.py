"""Numeric item labels; native source-view coordinates, not topology snaps."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import drawing,model_balloon as m


class BalloonDialog(W.QDialog):
    def __init__(self,ws,view,existing=None):
        stamp=m.signature(view,existing);initial=m.settings(existing) if existing else (1,0.,0.,20.,20.)
        super().__init__(ws.main)
        self.setObjectName('FullArcItemBalloon');self.setWindowTitle(tr('部品番号バルーン','Item Balloon'))
        self.view=view;self.existing=existing;self.stamp=stamp
        form=W.QFormLayout(self)
        note=W.QLabel(tr('番号は手入力です。BOMの自動連番・部品との関連付けはありません。\n座標は参照ビューの未拡大mm。ビューの移動と尺度に従います。辺への自動追従・スナップはありません。',
                        'Enter the item number manually; no automatic BOM numbering or component association.\nCoordinates are unscaled mm relative to the source view; they follow its position and scale. No edge tracking or snaps.'))
        note.setWordWrap(True);form.addRow(note)
        self.number=W.QSpinBox();self.number.setObjectName('balloonNumber');self.number.setRange(1,999999);self.number.setValue(initial[0]);form.addRow(tr('番号','Item Number'),self.number)
        self.fields=[]
        for label,value,name in zip((tr('矢印先端 X','Arrow Tip X'),tr('矢印先端 Y','Arrow Tip Y'),tr('バルーン中心 X','Bubble Center X'),tr('バルーン中心 Y','Bubble Center Y')),initial[1:],('originX','originY','bubbleX','bubbleY')):
            spin=W.QDoubleSpinBox();spin.setObjectName(name);spin.setRange(-1e6,1e6);spin.setDecimals(8);spin.setSuffix(' mm');spin.setValue(value);spin._baseline=(spin.value(),value);self.fields.append(spin);form.addRow(label,spin)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok)
        buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start();self.resize(650,340)

    def inputs(self):
        return (self.number.value(),)+tuple(s._baseline[1] if s.value()==s._baseline[0] else s.value() for s in self.fields)

    def refresh_guard(self):
        try:
            if m.signature(self.view,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:
            self.ok.setEnabled(False);self.status.setText(tr('参照ビュー・形状・バルーンが変わりました。閉じて開き直してください。','The view, geometry or balloon changed. Close and reopen.'))

    def accept(self):
        self.refresh_guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.view,*self.inputs(),existing=self.existing,expected=self.stamp)
        except Exception as error:self.status.setText(str(error));return
        super().accept()


def show(ws,existing=None):
    doc=drawing.ready(ws)
    if existing is None:
        selection=Gui.Selection.getSelectionEx()
        if len(selection)!=1 or selection[0].SubElementNames:
            raise ValueError(tr('投影図全体、または編集するバルーンを1つ選択してください。','Select one whole base view or an item balloon to edit.'))
        obj=selection[0].Object
        if obj.TypeId==m.TYPE and getattr(obj,'FluxBalloon',False):existing=obj
        else:view=obj
    if existing is not None:view=existing.SourceView
    page=m.target(view);dialog=BalloonDialog(ws,view,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:drawing.show(ws,page);return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
