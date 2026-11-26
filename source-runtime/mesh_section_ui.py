import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_section as backend

class MeshSectionDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source);self.centers=backend.centers(self.doc,source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshSection');self.setWindowTitle(tr('メッシュ断面スケッチ','Mesh Section Sketch'));form=W.QFormLayout(self)
        self.plane=W.QComboBox()
        for plane in ('XY','XZ','YZ'):self.plane.addItem(plane,plane)
        self.position=W.QDoubleSpinBox();self.position.setDecimals(8);self.position.setRange(-1000000,1000000);self.position.setSuffix(' mm');self.position.setValue(self.centers['XY'])
        self.angle_x=W.QDoubleSpinBox();self.angle_y=W.QDoubleSpinBox()
        for spin in (self.angle_x,self.angle_y):spin.setDecimals(8);spin.setRange(-180,180);spin.setSuffix(' °');spin.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        form.addRow(tr('基準平面','Guiding plane'),self.plane);form.addRow(tr('平面位置（全体座標）','Plane position (world)'),self.position)
        form.addRow(tr('基準平面X軸角度','Guiding-plane X angle'),self.angle_x);form.addRow(tr('基準平面Y軸角度','Guiding-plane Y angle'),self.angle_y)
        angle_note=W.QLabel(tr('基準平面の元のX軸、次に元のY軸で各±180°回転します。中心はXY:(0,0,位置)、XZ:(0,位置,0)、YZ:(位置,0,0)。位置は回転前の全体座標で、傾いた法線方向の距離ではありません。Fusionと同一の回転符号・操作軸を保証しません。','Rotate X then Y about the original guiding-plane axes, each ±180°. Pivot XY:(0,0,position),XZ:(0,position,0),YZ:(position,0,0). Position is the pre-rotation world coordinate, not distance along the tilted normal. Fusion manipulator axes/signs are not guaranteed identical.'));angle_note.setWordWrap(True);form.addRow(angle_note)
        note=W.QLabel(tr('メッシュ全体1～20000面と全体XY/XZ/YZ平面との交線を、編集可能な独立スケッチの線分にします。原本と表示状態を保持します。最大500線分・50断面群。native重複線を除き、端点を1e-6mm格子へ揃えます。native単精度の交点誤差を含み、平面へ投影する残差はmax(1e-5mm,全体座標最大絶対値×2e-7)以内に制限します。円弧／スプライン近似、参照平面、自動拘束、複数断面一括、原本追従・専用再編集は対象外です。接触・分岐断面は位置変更が必要な場合があります。','Creates editable independent sketch segments from one whole1–20000-facet mesh intersecting a world XY/XZ/YZ plane. Preserves the original and its visibility. Maximum500segments/50groups. Removes native duplicate segments and snaps endpoints to a1e-6mm grid. Includes native single-precision intersection error;projection residual is limited to max(1e-5mm,maximum absolute world coordinate×2e-7). No arc/spline fitting,reference planes,automatic constraints,multiple-plane batches,linked history or dedicated re-editing. Tangent/branching sections may require changing plane position.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.plane.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.plane_changed));self.position.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()
    def values(self):return self.plane.currentData(),self.position.value(),self.angle_x.value(),self.angle_y.value()
    def plane_changed(self,*_):self.position.setValue(self.centers[self.plane.currentData()]);self.invalidate()
    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.source.Name) is not self.source or self.ws.current_sketch() or backend.stamp(self.source)!=self.initial:raise ValueError(tr('文書または原本が変わりました。開き直してください。','The document or source changed. Reopen this dialog.'))
    def refresh_guard(self):
        try:self.guard()
        except Exception as e:self.invalidate();self.status.setText(str(e))
    def invalidate(self,*_):
        if self.overlay is not None:
            try:self.scene.removeChild(self.overlay)
            except RuntimeError:pass
        self.overlay=None;self.validated=None
        if hasattr(self,'ok'):self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();segments,placement=backend.section(self.doc,self.source,*self.values());points=[placement.multVec(v) for edge in segments for v in edge]
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);color=coin.SoBaseColor();color.rgb=(1.,.5,.1);node.addChild(color)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(p) for p in points]);node.addChild(coords);lines=coin.SoLineSet();lines.numVertices.setValues(0,len(segments),[2]*len(segments));node.addChild(lines);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(segments,placement));self.ok.setEnabled(True);self.status.setText(tr('断面線分数: %d','Section segments: %d')%len(segments))
        except Exception as e:self.status.setText(str(e))
    def accept(self):
        try:
            self.guard()
            if self.validated is None or self.validated[0]!=self.values():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            plane,position,ax,ay=self.values();self.result_object=backend.create(self.doc,self.source,plane,position,expected=self.validated[1],angle_x=ax,angle_y=ay);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as e:self.invalidate();self.status.setText(str(e))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('メッシュ全体を1つ選択してください。','Select one whole mesh.'))
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshSectionDialog(ws,source).exec_()
