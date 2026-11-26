"""Transient model-edge curvature comb. Closing removes Coin nodes; no document objects."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint,containers
import edge_comb_geometry as geometry

class EdgeCombDialog(W.QDialog):
    def __init__(self,ws,source,name):
        super().__init__(ws.main);self.ws=ws;self.doc=source.Document;self.source=source;self.overlay=None;self.scene=None;self.loaded=None;self.data=None
        self.setObjectName('FluxEdgeComb');self.setWindowTitle(tr('辺の曲率コーム解析','Edge Curvature Comb Analysis'));layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('1辺を弧長等間隔で標本化します。針は主法線方向、長さは曲率（1/mm）×倍率（mm²）です。標本間の不連続や曲率の最大値は保証しません。閉じると解析表示を削除し、ドキュメントには保存しません。','Samples one edge at equal arc-length intervals. Teeth follow the principal normal;length is curvature(1/mm)×scale(mm²). Samples do not guarantee detection of discontinuities or curvature extrema between samples. Closing removes the display;analysis is not saved in the document.'));note.setWordWrap(True);layout.addWidget(note);layout.addWidget(W.QLabel(source.Label));form=W.QFormLayout();layout.addLayout(form)
        self.edge=W.QComboBox();self.edge.addItems(['Edge'+str(i+1) for i in range(len(source.Shape.Edges))]);self.edge.setCurrentText(name);form.addRow(tr('辺','Edge'),self.edge);self.count=W.QSpinBox();self.count.setRange(5,200);self.count.setValue(31);form.addRow(tr('標本数','Samples'),self.count);self.scale=W.QDoubleSpinBox();self.scale.setDecimals(6);self.scale.setRange(.001,100000);self.scale.setValue(10.);self.scale.setSuffix(' mm²');form.addRow(tr('倍率','Scale'),self.scale);self.flip=W.QCheckBox(tr('表示方向を反転','Flip Display'));form.addRow(self.flip)
        for signal in (self.edge.currentIndexChanged,self.count.valueChanged,self.scale.valueChanged,self.flip.toggled):signal.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('解析表示','Analyze'));layout.addWidget(self.preview_button);self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Close);layout.addWidget(self.buttons);self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def stamp(self):return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in containers(self.source)),getattr(self.source,'Error',''),self.edge.currentText(),self.count.value(),self.scale.value(),self.flip.isChecked()
    def invalidate(self,*args):
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.data=None
        if hasattr(self,'status'):self.status.clear()
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            data=geometry.samples(self.doc,self.source,self.edge.currentText(),self.count.value(),self.scale.value(),self.flip.isChecked());node=coin.SoSeparator();color=coin.SoBaseColor();color.rgb=(1.,.55,.1);node.addChild(color);coords=coin.SoCoordinate3();points=[point for item in data for point in (item['point'],item['tip'])];coords.point.setValues(0,len(points),points);node.addChild(coords);lines=coin.SoLineSet();lines.numVertices.setValues(0,len(data),[2]*len(data));node.addChild(lines)
            base=coin.SoCoordinate3();base.point.setValues(0,len(data),[item['point'] for item in data]);node.addChild(base);curve=coin.SoLineSet();curve.numVertices=len(data);node.addChild(curve);self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.data=data;self.loaded=self.stamp();values=[item['curvature'] for item in data];self.status.setText(tr('標本上の曲率: 最小 %.9g / 最大 %.9g 1/mm','Sample curvature: min %.9g / max %.9g 1/mm')%(min(values),max(values)))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def refresh(self):
        if self.loaded is None:return
        try:
            if App.ActiveDocument!=self.doc or self.doc.getObject(self.source.Name)!=self.source or self.loaded!=self.stamp():raise ValueError(tr('入力が変わりました。再度解析してください。','Inputs changed. Analyze again.'))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or len(selected[0].SubElementNames)!=1:raise ValueError(tr('解析する辺を1本選択してください。','Select one explicit edge to analyze.'))
    source=selected[0].Object;name=selected[0].SubElementNames[0];geometry.samples(App.ActiveDocument,source,name);ws.region_picker.ticket+=1;ws.region_picker.clear();return EdgeCombDialog(ws,source,name).exec_()
