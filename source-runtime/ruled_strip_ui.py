"""Adjacent edge and planar face, transient boundary preview and linked editing."""
import FreeCAD as App
import FreeCADGui as Gui
import Part
from model_construction import element
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_ruled_strip as backend

class RuledStripDialog(W.QDialog):
    def __init__(self,ws,a,b,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=a[0].Document;self.sources=(a[0],b[0]);self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxRuledStrip');self.setWindowTitle(tr('辺から線織面','Ruled Surface From Edge'));layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('同じ原本の直線・円・円弧の境界辺と隣接する平面を選択します。法線または面内の横方向を基準に角度を指定します。面内方向は面法線×辺のパラメータ方向です。反転は全方向を反転します。楕円・楕円弧と非周期BSpline・Bezierは参照方向モードのみ対応します。自由曲線は次数1..9・制御点2..50に制限します。その他の曲線・曲面・連鎖選択は対象外です。円の半径がゼロを跨ぐ設定は拒否します。プレビューは輪郭線です。','Select a straight,circular or circular-arc boundary edge and adjacent planar face on the same source. Angle is relative to the normal or co-normal tangent. Co-normal is face normal × edge parameter direction. Reverse negates the full direction. Ellipses/elliptical arcs and nonperiodic BSpline/Bezier boundaries are available only in Reference Direction mode. Free curves require degree1..9 and2..50 poles. Other curves,curved faces and chains are excluded. Circular radius collapse or apex crossing is rejected. Preview shows the boundary.'));note.setWordWrap(True);layout.addWidget(note);self.fields=[]
        for source,name,kind in ((a[0],a[1],'Edge'),(b[0],b[1],'Face')):
            layout.addWidget(W.QLabel(source.Label));field=W.QComboBox();field.addItems([kind+str(i+1) for i in range(len(source.Shape.Edges if kind=='Edge' else source.Shape.Faces))]);field.setCurrentText(name);field.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));layout.addWidget(field);self.fields.append(field)
        form=W.QFormLayout();layout.addLayout(form);self.distance=W.QDoubleSpinBox();self.distance.setDecimals(9);self.distance.setRange(.001,100000);self.distance.setSuffix(' mm');self.distance.setValue(existing.Distance.Value if existing else 10.);self.angle=W.QDoubleSpinBox();self.angle.setDecimals(9);self.angle.setRange(-89,89);self.angle.setSuffix('°');self.angle.setValue(existing.Angle.Value if existing else 0.);self.mode=W.QComboBox();self.mode.addItem(tr('法線','Normal'),'normal');self.mode.addItem(tr('接線','Tangent'),'tangent');self.mode.addItem(tr('参照方向（角度0）','Reference Direction (Angle0)'),'direction');self.mode.setCurrentIndex(self.mode.findData(str(existing.DirectionMode) if existing else ('direction' if isinstance(element(a,'Edge').Curve,(Part.Ellipse,Part.BSplineCurve,Part.BezierCurve)) else 'normal')));self.reverse=W.QCheckBox(tr('反転','Reverse'));self.reverse.setChecked(bool(existing.Reverse) if existing else False)
        self.original=(existing.Distance.Value,existing.Angle.Value) if existing else (10.,0.);self.displayed=(self.distance.value(),self.angle.value())
        for text,field in ((tr('距離','Distance'),self.distance),(tr('角度','Angle'),self.angle),(tr('方向','Direction'),self.mode),('',self.reverse)):form.addRow(text,field)
        self.direction_source=W.QComboBox();self.direction_source.addItem(tr('方向の原本を選択','Select Direction Source'),None)
        for source in self.doc.Objects:
            if hasattr(source,'Shape') and not source.isDerivedFrom('App::Link') and not getattr(source,'FluxCADInternal',False) and source!=existing and (not existing or existing not in source.OutListRecursive):self.direction_source.addItem(source.Label,source.Name)
        ref=getattr(existing,'DirectionSource',None)
        if ref:self.direction_source.setCurrentIndex(self.direction_source.findData(ref.Name))
        self.direction_edge=W.QComboBox();source=self.doc.getObject(self.direction_source.currentData()) if self.direction_source.currentData() else None
        if source:self.direction_edge.addItems(['Edge'+str(i+1) for i in range(len(source.Shape.Edges))]+['Face'+str(i+1) for i in range(len(source.Shape.Faces))])
        self.direction_edge.setCurrentText(str(getattr(existing,'DirectionElement','Edge1')))
        self.direction_source_label=W.QLabel(tr('方向の原本','Direction Source'));self.direction_edge_label=W.QLabel(tr('直線辺・平面・構築形状','Straight Edge / Planar Face / Datum'));form.addRow(self.direction_source_label,self.direction_source);form.addRow(self.direction_edge_label,self.direction_edge)
        self.direction_source.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.direction_changed));self.direction_edge.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.direction_note=W.QLabel(tr('参照方向は直線辺・構築軸のパラメータ方向、または平面・構築平面の面法線です。平面の裏返しで方向も反転します。参照方向のみ楕円・楕円弧・非周期BSpline・Bezier境界にも対応します。角度は0、隣接平面に対する面外成分が必要です。反転で逆方向へ延ばします。','Reference direction uses a straight edge/axis parameter direction or planar face/datum-plane oriented normal. Reversing the planar face reverses this direction. Direction mode also accepts ellipse/elliptical-arc and nonperiodic BSpline/Bezier boundaries. Angle is0 and the direction must leave the adjacent plane. Reverse extends the other way.'));self.direction_note.setWordWrap(True);layout.addWidget(self.direction_note)
        self.angle_label=form.labelForField(self.angle)
        self.distance.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.angle.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.mode.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button);self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False);self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start();self.direction_fields()
    def direction_fields(self):
        enabled=self.mode.currentData()=='direction'
        for widget in (self.direction_source_label,self.direction_source,self.direction_edge_label,self.direction_edge,self.direction_note):widget.setVisible(enabled)
        self.angle.setVisible(not enabled);self.angle_label.setVisible(not enabled)
    def direction_changed(self,*args):
        self.direction_edge.clear();source=self.doc.getObject(self.direction_source.currentData()) if self.direction_source.currentData() else None
        if source:self.direction_edge.addItems(['Edge'+str(i+1) for i in range(len(source.Shape.Edges))]+['Face'+str(i+1) for i in range(len(source.Shape.Faces))])
        self.invalidate()
    def direction_values(self):
        if self.mode.currentData()!='direction':return {}
        return dict(direction_reference=self.doc.getObject(self.direction_source.currentData()) if self.direction_source.currentData() else None,direction_element=self.direction_edge.currentText())
    def direction_stamp(self):
        values=self.direction_values()
        if not values:return None
        from model_reference_pattern import reference_signature
        reference=values['direction_reference']
        if reference is None:raise ValueError('Select a direction reference')
        return reference.Name,values['direction_element'],reference_signature(reference)
    def values(self):
        self.distance.interpretText();self.angle.interpretText()
        distance,angle=tuple(original if field.value()==shown else field.value() for field,original,shown in zip((self.distance,self.angle),self.original,self.displayed))
        return distance,0. if self.mode.currentData()=='direction' else angle,self.mode.currentData(),self.reverse.isChecked()
    def refs(self):return tuple((source,field.currentText()) for source,field in zip(self.sources,self.fields))
    def stamp(self):
        backend.checked(self.doc,*self.refs(),self.existing)
        return self.values(),self.direction_stamp(),tuple((fingerprint(s),tuple(s.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(s)),name) for s,name in self.refs()),(self.existing.EdgeA,self.existing.FaceB,self.existing.Distance.Value,self.existing.Angle.Value,self.existing.DirectionMode,self.existing.Reverse,tuple(self.existing.getGlobalPlacement().toMatrix().A),getattr(self.existing,'DirectionSource',None).Name if getattr(self.existing,'DirectionSource',None) else None,str(getattr(self.existing,'DirectionElement',''))) if self.existing else None
    def invalidate(self,*args):
        self.direction_fields()
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            out=backend.preview(self.doc,*self.refs(),*self.values(),existing=self.existing,**self.direction_values());node=coin.SoSeparator();color=coin.SoBaseColor();color.rgb=(1.,.55,.1);node.addChild(color)
            for boundary in out.Edges:
                points=boundary.discretize(Number=129);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(point) for point in points]);node.addChild(coords);line=coin.SoLineSet();line.numVertices=len(points);node.addChild(line)
            self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.loaded=self.stamp();self.ok.setEnabled(True);self.status.setText(tr('面積: ','Area: ')+('%.9g mm²'%out.Area))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def guard(self):
        if App.ActiveDocument!=self.doc or self.loaded is None or self.loaded!=self.stamp():raise ValueError(tr('入力が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def refresh(self):
        if self.loaded is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:self.guard();self.invalidate();self.result_object=backend.apply(self.doc,*self.refs(),*self.values(),existing=self.existing,**self.direction_values());Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx();existing=None;refs=[]
    if len(selected)==1 and getattr(selected[0].Object,'FluxRuledStrip',False) and not selected[0].SubElementNames:
        existing=selected[0].Object;refs=[(existing.SourceA,existing.EdgeA),(existing.SourceB,existing.FaceB)]
    else:
        for item in selected:
            for name in item.SubElementNames:refs.append((item.Object,name))
    if len(refs)!=2:raise ValueError(tr('直線・円・楕円またはその円弧の境界辺と平面を1つずつ選択してください。','Select one line/circle/ellipse/arc boundary edge and one planar face.'))
    if existing is None:
        edges=[ref for ref in refs if ref[1].startswith('Edge')];faces=[ref for ref in refs if ref[1].startswith('Face')]
        if len(edges)!=1 or len(faces)!=1:raise ValueError('Select one Edge and one Face.')
        refs=edges+faces
    if existing:backend.checked(App.ActiveDocument,*refs,existing)
    elif isinstance(element(refs[0],'Edge').Curve,(Part.Ellipse,Part.BSplineCurve,Part.BezierCurve)):
        backend.preview(App.ActiveDocument,*refs,mode='direction',direction_reference=refs[1][0],direction_element=refs[1][1])
    else:backend.preview(App.ActiveDocument,*refs)
    ws.region_picker.ticket+=1;ws.region_picker.clear();return RuledStripDialog(ws,*refs,existing).exec_()
