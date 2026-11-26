"""Single-edge SheetMetal hem dialog in Japanese and English."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_hem as m

class HemDialog(W.QDialog):
    def __init__(self,ws,source,edge,existing=None):
        stamp=m.signature(source,edge,existing)
        super().__init__(ws.main);self.setObjectName('FullArcHem');self.setWindowTitle(tr('ヘム（折返し）','Hem'))
        self.ws=ws;self.source=source;self.edge=edge;self.existing=existing;self.stamp=stamp
        values=m.settings(existing) if existing else dict(kind='Open',width=10.,opening=1.,radius=1.,include_bend=True,invert=False)
        form=W.QFormLayout(self);hint=W.QLabel(tr('直線の辺1つを折り返します。フラット／オープン／閉じた涙形／閉じたロール。\n材料外側・単一辺、ミター／隙間／リリーフ／多辺／製造可否保証なし。辺の位相変更は再選択してください。',
        'Fold one straight edge:flat,open,closed teardrop or closed rolled.\nMaterial outside,single edge. No miter,gaps,relief,multiple edges or manufacturing certification. Reselect after topology changes.'));hint.setWordWrap(True);form.addRow(hint)
        form.addRow(tr('参照','Reference'),W.QLabel(source.Label+' · '+edge))
        self.kind=W.QComboBox()
        for label,key in [(tr('フラット','Flat'),'Flat'),(tr('オープン','Open'),'Open'),(tr('涙形（閉）','Teardrop (closed)'),'Teardrop'),(tr('ロール（閉）','Rolled (closed)'),'Rolled')]:self.kind.addItem(label,key)
        self.kind.setCurrentIndex(self.kind.findData(values['kind']));form.addRow(tr('種類','Type'),self.kind)
        self.fields={}
        for key,label in [('width',tr('折返し幅','Hem Width')),('opening',tr('開口隙間','Opening Gap')),('radius',tr('内側半径','Inner Radius'))]:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(.001,100000);spin.setValue(values[key]);spin.setSuffix(' mm');spin._baseline=(spin.value(),values[key]);self.fields[key]=spin;form.addRow(label,spin)
        self.include=W.QCheckBox(tr('幅に曲げを含む','Include bend in width'));self.include.setChecked(values['include_bend']);form.addRow(self.include)
        self.reverse=W.QCheckBox(tr('反転','Reverse'));self.reverse.setChecked(values['invert']);form.addRow(self.reverse)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.kind.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.changed));self.changed()
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start();self.resize(620,380)
    def changed(self):
        kind=self.kind.currentData();self.fields['width'].setEnabled(kind!='Rolled');self.include.setEnabled(kind!='Rolled');self.fields['opening'].setEnabled(kind=='Open');self.fields['radius'].setEnabled(kind in ('Teardrop','Rolled'))
    def inputs(self):
        values={k:(s._baseline[1] if s.value()==s._baseline[0] else s.value()) for k,s in self.fields.items()}
        values.update(kind=self.kind.currentData(),include_bend=self.include.isChecked(),invert=self.reverse.isChecked());return values
    def guard(self):
        try:
            if m.signature(self.source,self.edge,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('参照・形状・設定が変わりました。閉じて開き直してください。','Inputs,geometry or settings changed. Close and reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.source,self.edge,existing=self.existing,expected=self.stamp,**self.inputs())
        except Exception as error:self.status.setText(str(error));return
        super().accept()

def show(ws,existing=None):
    if App.ActiveDocument is None or ws.current_sketch() or Gui.Control.activeDialog():raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active operation.'))
    if existing is None:
        selected=Gui.Selection.getSelectionEx()
        if len(selected)!=1:raise ValueError(tr('直線の辺1つ、またはヘム全体を選択してください。','Select one straight edge or a whole hem.'))
        entry=selected[0]
        if getattr(entry.Object,'FluxHem',False) and not entry.SubElementNames:existing=entry.Object
        else:
            if len(entry.SubElementNames)!=1:raise ValueError(tr('直線の辺1つを選択してください。','Select one straight edge.'))
            source=entry.Object;edge=entry.SubElementNames[0]
    if existing is not None:source=existing.Source;edge=existing.Edge
    dialog=HemDialog(ws,source,edge,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:ws.compact();return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
