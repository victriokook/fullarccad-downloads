import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_reduce as backend


class MeshReduceDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshReduce');self.setWindowTitle(tr('メッシュ面数を削減','Reduce Mesh Facets'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label));self.tolerance=W.QDoubleSpinBox();self.tolerance.setDecimals(8);self.tolerance.setRange(1e-6,1000);self.tolerance.setValue(.1);self.tolerance.setSuffix(' mm')
        self.reduction=W.QDoubleSpinBox();self.reduction.setDecimals(6);self.reduction.setRange(.1,95);self.reduction.setValue(50);self.reduction.setSuffix(' %')
        form.addRow(tr('native許容差','Native tolerance'),self.tolerance);form.addRow(tr('削減率の目標上限','Reduction goal upper limit'),self.reduction)
        note=W.QLabel(tr('閉じた単一メッシュ4～20000面を対象に、原本を保持・非表示にして独立結果を作成します。許容差によって目標率まで減らない場合があります。全表面偏差の保証、開メッシュ、面グループ、正確な目標面数、追従履歴・専用再編集、面別色の保持は対象外です。',
            'For one closed mesh with4–20000 facets. Retains and hides the original;creates an independent result. Native tolerance may prevent reaching the reduction goal. No global surface-deviation guarantee,open meshes,face groups,exact target counts,linked history/dedicated re-editing or per-facet color preservation.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.tolerance.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reduction.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return self.tolerance.value(),self.reduction.value()/100

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
            self.guard();mesh,pose=backend.reduce(self.doc,self.source,*self.values());points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(pose.multVec(p)) for p in points]);node.addChild(coords)
            faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(mesh));self.ok.setEnabled(True);self.status.setText(tr('面数: %d → %d（実削減率 %.3f%%）','Facets: %d → %d(actual reduction %.3f%%)')%(self.source.Mesh.CountFacets,mesh.CountFacets,100*(1-mesh.CountFacets/self.source.Mesh.CountFacets)))
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
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshReduceDialog(ws,source).exec_()
