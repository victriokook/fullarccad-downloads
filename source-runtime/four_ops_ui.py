import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import four_ops as m
class OperationDialog(W.QDialog):
    def __init__(self,ws,kind,sources,elements,existing=None):
        self.options=m.settings(existing) if existing else dict(m.module(kind).DEFAULTS)
        self.stamp=m.signature(kind,sources,elements,self.options,existing)
        super().__init__(ws.main);self.setObjectName('FullArcFourOperation');self.setWindowTitle(tr(*m.module(kind).TITLE));self.kind=kind;self.sources=sources;self.elements=elements;self.existing=existing
        form=W.QFormLayout(self);hint=W.QLabel(tr(*m.module(kind).HINT));hint.setWordWrap(True);form.addRow(hint)
        form.addRow(tr('参照','References'),W.QLabel(' / '.join(s.Label for s in sources)+' '+','.join(elements)))
        self.fields={}
        for key,ja,en,lo,hi in m.module(kind).FIELDS:
            spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(lo,hi);spin.setValue(self.options[key]);spin._baseline=(spin.value(),self.options[key]);self.fields[key]=spin;form.addRow(tr(ja,en),spin)
        self.flags={}
        for key,ja,en in m.module(kind).FLAGS:
            box=W.QCheckBox(tr(ja,en));box.setChecked(self.options[key]);self.flags[key]=box;form.addRow(box)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start();self.resize(650,350)
    def inputs(self):
        values=dict(self.options)
        for k,s in self.fields.items():values[k]=s._baseline[1] if s.value()==s._baseline[0] else s.value()
        for k,s in self.flags.items():values[k]=s.isChecked()
        return values
    def guard(self):
        try:
            if m.signature(self.kind,self.sources,self.elements,self.options,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('参照・設定が変わりました。閉じて再選択してください。','Inputs or settings changed. Close and reselect.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.kind,self.sources,self.elements,self.inputs(),self.existing,self.stamp)
        except Exception as error:self.status.setText(str(error));return
        super().accept()
def show(ws,kind,existing=None):
    if App.ActiveDocument is None or ws.current_sketch() or Gui.Control.activeDialog():raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active operation.'))
    selected=Gui.Selection.getSelectionEx()
    if existing is None and len(selected)==1 and not selected[0].SubElementNames and getattr(selected[0].Object,'FluxFourOp',False):existing=selected[0].Object
    if existing is not None:
        if existing.Operation!=kind:raise ValueError('Select the same operation type')
        sources=list(existing.InputObjects);elements=list(existing.Elements)
    else:sources,elements=m.module(kind).selection(selected)
    dialog=OperationDialog(ws,kind,sources,elements,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:ws.compact();return dialog.result_object
    finally:dialog.timer.stop();dialog.deleteLater()
