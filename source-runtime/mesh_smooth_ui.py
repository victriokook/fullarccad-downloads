import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_smooth as backend


class MeshSmoothDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshSmooth');self.setWindowTitle(tr('メッシュを平滑化','Smooth Mesh'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label));self.iterations=W.QSpinBox();self.iterations.setRange(1,20);self.iterations.setValue(5)
        self.strength=W.QDoubleSpinBox();self.strength.setDecimals(8);self.strength.setRange(.01,.5);self.strength.setValue(.3)
        form.addRow(tr('反復回数','Iterations'),self.iterations);form.addRow(tr('native平滑化係数λ','Native smoothing factor λ'),self.strength)
        note=W.QLabel(tr('閉じた単一メッシュ4～20000面をnative Laplaceで平滑化します。面数と接続を維持し、原本を保持・非表示にして独立結果を作ります。寸法・角・体積は変化します。λはFreeCADの係数で、FusionのSmoothnessと同じ尺度ではありません。体積・鋭角の保持、部分面、開メッシュ、追従履歴・専用再編集・面別色保持は対象外です。','Smooths one closed mesh with4–20000 facets using native Laplace. Preserves facet connectivity/count;retains and hides the original and creates an independent result. Dimensions,corners and volume change. λ is the FreeCAD coefficient,not the same scale as Fusion Smoothness. No volume/sharp-feature preservation,partial faces,open meshes,linked history/dedicated re-editing or per-facet colors.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.iterations.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.strength.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return self.iterations.value(),self.strength.value()

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.source.Name) is not self.source or self.ws.current_sketch() or backend.stamp(self.source)!=self.initial:
            raise ValueError(tr('文書またはメッシュが変わりました。開き直してください。','The document or mesh changed. Reopen this dialog.'))

    def refresh_guard(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def invalidate(self,*_):
        if self.overlay is not None:
            try:self.scene.removeChild(self.overlay)
            except RuntimeError:pass
        self.overlay=None;self.validated=None
        if hasattr(self,'ok'):self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();mesh,pose=backend.smooth(self.doc,self.source,*self.values());points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(pose.multVec(p)) for p in points]);node.addChild(coords)
            faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(mesh));self.ok.setEnabled(True);self.status.setText(tr('面数: %d（維持） / 体積: %.6g mm³','Facets: %d(preserved) / Volume: %.6g mm³')%(mesh.CountFacets,mesh.Volume))
        except Exception as error:self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated is None or self.validated[0]!=self.values():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_object=backend.create(self.doc,self.source,*self.values(),expected=self.validated[1]);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def done(self,result):self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('メッシュ全体を1つ選択してください。','Select one whole mesh.'))
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshSmoothDialog(ws,source).exec_()
