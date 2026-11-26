"""Compact controls for saved glTF assets."""
from i18n import tr
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtGui
_panel=None

class Panel(QtGui.QDockWidget):
    def __init__(self,root):
        super().__init__(tr('glTF 表示設定'),Gui.getMainWindow());self.root=root
        self.setObjectName('FullArcCAD_glTFControls')
        body=QtGui.QWidget();layout=QtGui.QFormLayout(body);self.setWidget(body)
        self.variant=QtGui.QComboBox();self.variant.addItems(root.getEnumerationsOfProperty('MaterialVariant'));self.variant.setItemText(0,tr('元の材質'));self.variant.setCurrentIndex(root.VariantIndex+1)
        self.animation=QtGui.QComboBox();self.animation.addItems(root.getEnumerationsOfProperty('Animation'));self.animation.setItemText(0,tr('なし'));self.animation.setCurrentIndex(root.AnimationIndex+1)
        self.time=QtGui.QDoubleSpinBox();self.time.setDecimals(2);self.time.setRange(0,max([a['duration'] for a in __import__('gltf_import').runtime(root).animations]+[0]));self.time.setSingleStep(.1);self.time.setSuffix(' s')
        self.play=QtGui.QPushButton(tr('再生 / 停止'));self.play.setCheckable(True)
        layout.addRow(tr('材質'),self.variant);layout.addRow(tr('アニメーション'),self.animation);layout.addRow(tr('時刻'),self.time);layout.addRow(self.play)
        note=QtGui.QLabel(tr('透過は薄いガラスの近似表示です。'));note.setWordWrap(True);layout.addRow(note)
        self.variant.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda i:setattr(self.root,'MaterialVariant',i),(1, 1, False, False)))
        self.animation.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda i:setattr(self.root,'Animation',i),(1, 1, False, False)))
        self.time.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda t:setattr(self.root,'AnimationTime',t),(1, 1, False, False)))
        self.play.toggled.connect(__import__('builtins')._fullarc_qt_slot(lambda v:setattr(self.root,'Play',v),(1, 1, False, False)))
        self.timer=QtCore.QTimer(self);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start(100)
    def refresh(self):
        try:
            if App.ActiveDocument is not self.root.Document:return
            for widget,value in ((self.time,float(self.root.AnimationTime)),(self.play,self.root.Play)):
                widget.blockSignals(True)
                if widget is self.time:widget.setValue(value)
                else:widget.setChecked(value)
                widget.blockSignals(False)
        except (RuntimeError,ReferenceError):self.timer.stop();self.close()

def show(root):
    global _panel
    if _panel is not None:_panel.timer.stop();_panel.close();_panel.deleteLater()
    _panel=Panel(root);Gui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea,_panel);_panel.show()

def show_current():
    doc=App.ActiveDocument
    roots=[o for o in doc.Objects if getattr(o,'IsGltfAsset',False)] if doc else []
    selected=[]
    for obj in Gui.Selection.getSelection():
        root=obj if getattr(obj,'IsGltfAsset',False) else getattr(obj,'Asset',None)
        if root in roots and root not in selected:selected.append(root)
    if len(selected)==1:return show(selected[0])
    if len(roots)==1:return show(roots[0])
    raise ValueError(tr('glTFモデルのメッシュを1つ選択してください。'))
