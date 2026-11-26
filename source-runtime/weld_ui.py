import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import drawing,model_weld as m
class WeldDialog(W.QDialog):
    def __init__(self,ws,view,existing=None):
        self.stamp=m.signature(view,existing);super().__init__(ws.main);self.view=view;self.existing=existing;self.setObjectName('FullArcWeld');self.setWindowTitle(tr('溶接記号','Welding Symbol'))
        values=m.settings(existing) if existing else dict(kind='Fillet',points=((0.,0.),(15.,15.),(35.,15.)),left='',center='',right='',tail='',both=False,around=False,field=False)
        form=W.QFormLayout(self);hint=W.QLabel(tr('native AWS形式タイルによる手入力記号。用紙mm、3点引出線の末尾は水平。\nすみ肉／I形／V形。辺追従・自動溶接判定・規格適合認証・形状プレビューなし。','Manual native AWS-style tiles,printed mm,three-point leader with horizontal tail.\nFillet/square/V. No edge attachment,automatic weld detection,standards certification or geometry preview.'));hint.setWordWrap(True);form.addRow(hint)
        self.kind=W.QComboBox()
        for label,key in [(tr('すみ肉','Fillet'),'Fillet'),(tr('I形','Square groove'),'Square'),(tr('V形','V groove'),'V')]:self.kind.addItem(label,key)
        self.kind.setCurrentIndex(self.kind.findData(values['kind']));form.addRow(tr('記号','Symbol'),self.kind);self.texts={}
        for key,ja,en in [('left','左の寸法','Left Text'),('center','中央の注記','Center Text'),('right','右の寸法','Right Text'),('tail','尾の注記','Tail Text')]:
            edit=W.QLineEdit(values[key]);edit.setMaxLength(80);self.texts[key]=edit;form.addRow(tr(ja,en),edit)
        self.coords=[]
        for i,pt in enumerate(values['points']):
            for axis,value in zip('XY',pt):
                spin=W.QDoubleSpinBox();spin.setDecimals(8);spin.setRange(-1e6,1e6);spin.setValue(value);spin._baseline=(spin.value(),value);self.coords.append(spin);form.addRow(str(i+1)+' '+axis+' mm',spin)
        self.flags={}
        for key,ja,en in [('both','両側記号','Both Sides'),('around','全周','All Around'),('field','現場溶接','Field Weld')]:
            box=W.QCheckBox(tr(ja,en));box.setChecked(values[key]);self.flags[key]=box;form.addRow(box)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);self.ok=buttons.button(W.QDialogButtonBox.Ok);buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));form.addRow(buttons);self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.timer.start()
    def inputs(self):
        xy=[s._baseline[1] if s.value()==s._baseline[0] else s.value() for s in self.coords]
        return dict(kind=self.kind.currentData(),points=tuple(tuple(xy[i:i+2]) for i in (0,2,4)),**{k:v.text() for k,v in self.texts.items()},**{k:v.isChecked() for k,v in self.flags.items()})
    def guard(self):
        try:
            if m.signature(self.view,self.existing)!=self.stamp:raise ValueError('stale')
        except Exception:self.ok.setEnabled(False);self.status.setText(tr('参照・記号が変わりました。開き直してください。','View or symbol changed. Reopen.'))
    def accept(self):
        self.guard()
        if not self.ok.isEnabled():return
        try:self.result_object=m.apply(self.view,existing=self.existing,expected=self.stamp,**self.inputs())
        except Exception as error:self.status.setText(str(error));return
        super().accept()
def show(ws):
    drawing.ready(ws);selected=Gui.Selection.getSelectionEx();existing=None
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('投影図全体か溶接記号を選択してください。','Select a whole drawing view or welding symbol.'))
    obj=selected[0].Object
    if getattr(obj,'FluxWeld',False):existing=obj;view=m.check(obj).LeaderParent
    elif getattr(obj,'FluxWeldLeader',False):
        matches=[x for x in obj.InList if getattr(x,'FluxWeld',False) and x.Leader==obj]
        if len(matches)!=1:raise ValueError('Missing weld symbol')
        existing=matches[0];view=obj.LeaderParent
    else:view=obj
    dialog=WeldDialog(ws,view,existing)
    try:
        if dialog.exec_()==W.QDialog.Accepted:drawing.show(ws,m.drawing.page_of(view))
    finally:dialog.timer.stop();dialog.deleteLater()
