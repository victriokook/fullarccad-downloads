import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_fill as backend


class MeshFillDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshFill');self.setWindowTitle(tr('メッシュの穴を埋める','Fill Mesh Holes'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label))
        self.maximum=W.QSpinBox();self.maximum.setRange(3,200);self.maximum.setValue(200);form.addRow(tr('穴ごとの最大辺数','Maximum edges per hole'),self.maximum)
        note=W.QLabel(tr('開口付きの向きが整合した単一メッシュ4～20000面を対象に、全ての穴をnative平坦三角形で埋め、閉じた非零体積の独立結果を作ります。既存の頂点・面を保持し、原本は保持・非表示にします。境界合計200辺・20穴まで。全ての穴が指定辺数以内である必要があります。元の曲面・曲率の復元、穴の個別選択、部分的な穴埋め、法線自動整合、自己交差／非多様体修復、追従履歴・専用再編集・面別色保持は対象外です。','Fills all holes of one oriented mesh with4–20000 facets using native flat triangulation;requires a closed nonzero-volume independent result. Preserves existing vertices/facets and retains/hides the original. Total boundary limit200edges/20holes;every hole must fit the edge limit. No original-surface/curvature restoration,individual-hole selection,partial filling,automatic normal harmonization,self-intersection/nonmanifold repair,linked history/dedicated re-editing or per-facet colors.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.maximum.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return (self.maximum.value(),)

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
            self.guard();mesh,pose=backend.fill(self.doc,self.source,*self.values());points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(pose.multVec(p)) for p in points]);node.addChild(coords)
            faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(mesh));self.ok.setEnabled(True);self.status.setText(tr('穴数: %d → 0 / 面数: %d → %d','Holes: %d → 0 / Facets: %d → %d')%(len(backend.boundaries(self.source.Mesh)),self.source.Mesh.CountFacets,mesh.CountFacets))
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
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshFillDialog(ws,source).exec_()
