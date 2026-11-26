"""Transient colored Gaussian-curvature point samples."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint,containers
from edge_comb_ui import EdgeCombDialog
import surface_curvature_geometry as geometry

class SurfaceCurvatureDialog(EdgeCombDialog):
    def __init__(self,ws,source,name):
        W.QDialog.__init__(self,ws.main);self.ws=ws;self.doc=source.Document;self.source=source;self.overlay=None;self.scene=None;self.loaded=None;self.data=None
        self.setWindowTitle(tr('面の曲率標本解析','Surface Curvature Samples'));self.setObjectName('FluxSurfaceCurvature');layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('主曲率は基底曲面の符号で、面の表裏反転では符号が変わりません。Fusionの閾値判定色とは異なります。面内のUV格子点を色表示します（弧長等間隔ではありません）。青:負、緑:0、赤:正。±色限界で飽和します。穴の中は除外します。連続した曲率マップではなく、標本間の極値や不連続は保証しません。閉じると消去し、保存しません。','Principal curvature signs follow the basis surface,not reversed/outward face normals. Colors use signed saturation,not Fusion threshold classification. Colors UV grid samples on one face (not equal physical spacing). Blue:negative,green:zero,red:positive,saturated at ±Color Limit. Holes are excluded. This is not a continuous map;extrema or discontinuities between samples are not guaranteed. Closing removes the display;analysis is not saved.'));note.setWordWrap(True);layout.addWidget(note);layout.addWidget(W.QLabel(source.Label));form=W.QFormLayout();layout.addLayout(form)
        self.face=W.QComboBox();self.face.addItems(['Face'+str(i+1) for i in range(len(source.Shape.Faces))]);self.face.setCurrentText(name);form.addRow(tr('面','Face'),self.face)
        self.mode=W.QComboBox();self.mode.addItem(tr('ガウス曲率','Gaussian'),'gaussian');self.mode.addItem(tr('最小主曲率','Principal Minimum'),'principal_min');self.mode.addItem(tr('最大主曲率','Principal Maximum'),'principal_max');form.addRow(tr('種類','Type'),self.mode)
        self.count=W.QSpinBox();self.count.setRange(5,50);self.count.setValue(15);form.addRow(tr('各方向の標本数','Samples per Direction'),self.count)
        self.limit=W.QDoubleSpinBox();self.limit.setDecimals(12);self.limit.setRange(1e-12,1e6);self.limit.setValue(.01);self.limit.setSuffix(' 1/mm²');form.addRow(tr('色限界（絶対値）','Color Limit (absolute)'),self.limit)
        for signal in (self.face.currentIndexChanged,self.count.valueChanged,self.limit.valueChanged):signal.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.mode.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.mode_changed))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('解析表示','Analyze'));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Close);self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));layout.addWidget(self.buttons);self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def mode_changed(self,*args):
        self.invalidate();self.limit.setSuffix(' 1/mm²' if self.mode.currentData()=='gaussian' else ' 1/mm')
    def stamp(self):return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in containers(self.source)),getattr(self.source,'Error',''),self.face.currentText(),self.count.value(),self.limit.value(),self.mode.currentData()
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            data=geometry.samples(self.doc,self.source,self.face.currentText(),self.count.value(),self.limit.value(),self.mode.currentData());node=coin.SoSeparator();style=coin.SoDrawStyle();style.pointSize=7.;node.addChild(style)
            binding=coin.SoMaterialBinding();binding.value=coin.SoMaterialBinding.PER_VERTEX;node.addChild(binding);colors=coin.SoBaseColor();colors.rgb.setValues(0,len(data),[x['color'] for x in data]);node.addChild(colors)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(data),[x['point'] for x in data]);node.addChild(coords);points=coin.SoPointSet();points.numPoints=len(data);node.addChild(points)
            self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.data=data;self.loaded=self.stamp();values=[x['value'] for x in data];self.status.setText(tr('%d標本 / 最小 %.9g 最大 %.9g %s','%d samples / min %.9g max %.9g %s')%(len(data),min(values),max(values),'1/mm²' if self.mode.currentData()=='gaussian' else '1/mm'))
        except Exception as error:self.invalidate();self.status.setText(str(error))

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or len(selected[0].SubElementNames)!=1:raise ValueError(tr('解析する面を1枚選択してください。','Select one explicit face to analyze.'))
    source=selected[0].Object;name=selected[0].SubElementNames[0];geometry.samples(App.ActiveDocument,source,name);ws.region_picker.ticket+=1;ws.region_picker.clear();return SurfaceCurvatureDialog(ws,source,name).exec_()
