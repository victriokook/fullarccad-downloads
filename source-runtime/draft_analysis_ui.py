"""Transient colored draft-angle samples with an optional straight reference edge."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint,containers
from edge_comb_ui import EdgeCombDialog
import draft_analysis_geometry as geometry

class DraftAnalysisDialog(EdgeCombDialog):
    def __init__(self,ws,source,name):
        W.QDialog.__init__(self,ws.main);self.ws=ws;self.doc=source.Document;self.source=source;self.overlay=None;self.scene=None;self.loaded=None;self.data=None
        self.setWindowTitle(tr('面の抜き勾配標本解析','Surface Draft Angle Samples'));self.setObjectName('FluxDraftAnalysis');layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('ワールドXYZまたは参照原本の直線EdgeN（構築軸のEdge1を含む）を抜き方向に指定します。参照方向は辺のnativeパラメータ方向で、表裏反転だけでは変わらない場合があります。反転チェックで確実に反転できます。0°は抜き方向と面が平行、+90°は法線が同方向、-90°は逆方向です。青:負、緑:0、赤:正。色限界で飽和します。UV標本であり連続マップや型から抜ける保証ではありません。穴を除外し、閉じると消去・保存しません。','Select world XYZ or one straight reference EdgeN (including construction-axis Edge1). Reference direction follows native edge parameters;reversing topology alone may not flip it. Use Reverse Pull to flip explicitly. Zero means the surface is parallel to pull;+90 means normal along pull;-90 opposite. Blue:negative,green:zero,red:positive,saturated at the angle limit. UV point samples are not a continuous map or mold-release guarantee. Holes are excluded. Closing removes the display;analysis is not saved.'));note.setWordWrap(True);layout.addWidget(note);layout.addWidget(W.QLabel(source.Label));form=W.QFormLayout();layout.addLayout(form)
        self.face=W.QComboBox();self.face.addItems(['Face'+str(i+1) for i in range(len(source.Shape.Faces))]);self.face.setCurrentText(name);form.addRow(tr('面','Face'),self.face)
        self.count=W.QSpinBox();self.count.setRange(5,50);self.count.setValue(15);form.addRow(tr('各方向の標本数','Samples per Direction'),self.count)
        self.angle=W.QDoubleSpinBox();self.angle.setDecimals(6);self.angle.setRange(.001,90);self.angle.setValue(3.);self.angle.setSuffix('°');form.addRow(tr('色角度限界（絶対値）','Color Angle Limit (absolute)'),self.angle)
        self.axis=W.QComboBox();self.axis.addItems(['X','Y','Z']);self.axis.addItem(tr('参照辺','Reference Edge'),'Reference');self.axis.setCurrentText('Z');form.addRow(tr('ワールド抜き方向','World Pull Direction'),self.axis);self.reverse=W.QCheckBox(tr('抜き方向を反転','Reverse Pull'));form.addRow(self.reverse)
        self.reference_source=W.QComboBox()
        for obj in self.doc.Objects:
            if hasattr(obj,'Shape'):self.reference_source.addItem(obj.Label+' ('+obj.Name+')',obj.Name)
        form.addRow(tr('方向の参照原本','Direction Reference Source'),self.reference_source);self.reference_edge=W.QLineEdit('Edge1');form.addRow(tr('参照辺（EdgeN）','Reference Edge (EdgeN)'),self.reference_edge)
        self.reference_source.setEnabled(False);self.reference_edge.setEnabled(False);self.reference_source.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reference_edge.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.axis.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.direction_changed))
        for signal in (self.face.currentIndexChanged,self.count.valueChanged,self.angle.valueChanged,self.axis.currentIndexChanged,self.reverse.toggled):signal.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('解析表示','Analyze'));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Close);self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));layout.addWidget(self.buttons);self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def axis_code(self):return self.axis.currentData() or self.axis.currentText()
    def reference_object(self):return self.doc.getObject(self.reference_source.currentData() or '') if self.axis_code()=='Reference' else None
    def direction_changed(self,*args):
        active=self.axis_code()=='Reference';self.reference_source.setEnabled(active);self.reference_edge.setEnabled(active);self.invalidate()
    def reference_stamp(self):
        if self.axis_code()!='Reference':return None
        ref=self.reference_object();geometry.reference_direction(self.doc,ref,self.reference_edge.text())
        return ref.Name,fingerprint(ref),tuple(ref.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in containers(ref)),tuple((o.Name,tuple(o.State),getattr(o,'Error','')) for o in [ref]+ref.OutListRecursive),self.reference_edge.text()
    def stamp(self):return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in containers(self.source)),getattr(self.source,'Error',''),self.face.currentText(),self.count.value(),self.angle.value(),self.axis_code(),self.reverse.isChecked(),self.reference_stamp()
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            data=geometry.samples(self.doc,self.source,self.face.currentText(),self.count.value(),self.angle.value(),self.axis_code(),self.reverse.isChecked(),self.reference_object(),self.reference_edge.text());node=coin.SoSeparator();style=coin.SoDrawStyle();style.pointSize=7.;node.addChild(style)
            binding=coin.SoMaterialBinding();binding.value=coin.SoMaterialBinding.PER_VERTEX;node.addChild(binding);colors=coin.SoBaseColor();colors.rgb.setValues(0,len(data),[x['color'] for x in data]);node.addChild(colors)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(data),[x['point'] for x in data]);node.addChild(coords);points=coin.SoPointSet();points.numPoints=len(data);node.addChild(points)
            self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.data=data;self.loaded=self.stamp();values=[x['draft'] for x in data];self.status.setText(tr('%d標本 / 抜き勾配 最小 %.9g 最大 %.9g °','%d samples / Draft min %.9g max %.9g °')%(len(data),min(values),max(values)))
        except Exception as error:self.invalidate();self.status.setText(str(error))

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or len(selected[0].SubElementNames)!=1:raise ValueError(tr('解析する面を1枚選択してください。','Select one explicit face to analyze.'))
    source=selected[0].Object;name=selected[0].SubElementNames[0];geometry.samples(App.ActiveDocument,source,name);ws.region_picker.ticket+=1;ws.region_picker.clear();return DraftAnalysisDialog(ws,source,name).exec_()
