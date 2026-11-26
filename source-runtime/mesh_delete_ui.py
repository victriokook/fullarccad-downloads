import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_delete as backend


class MeshDeleteDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshDelete');self.setWindowTitle(tr('メッシュ面を削除','Delete Mesh Faces'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label));self.faces=W.QLineEdit('1');form.addRow(tr('削除する面番号（例 1,3-5）','Faces to delete (e.g. 1,3-5)'),self.faces)
        note=W.QLabel(tr('現在の三角形の1始まり番号を指定します。残す面は青、削除面は赤でプレビューします。原本を保持・非表示にして独立結果を作成し、残る頂点と向きを保持します。入力2～20000面、全削除・重複番号は拒否。面順序が変わると開き直しが必要です。穴埋め、画面上の個別面ピック、面グループ／面別色、追従履歴・専用再編集は対象外です。',
            'Use current triangle numbers starting at1. Preview: blue retained, red deleted. Retains and hides original; creates an independent result preserving remaining vertices and orientation. Input2–20000 facets; rejects all deletion or repeated indices. Reopen after facet-order changes. No filling, individual canvas facet picking, face groups/per-facet colors, linked history or dedicated re-editing.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.faces.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return (self.faces.text(),)

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
            self.guard();mesh,pose=backend.remove(self.doc,self.source,*self.values());points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(pose.multVec(p)) for p in points]);node.addChild(coords)
            faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);removed,_=backend.validate(self.doc,self.source);removed=removed.meshFromSegment(list(backend.indices(self.faces.text(),removed.CountFacets)));rp,rf=removed.Topology
            red=coin.SoMaterial();red.diffuseColor=(1,.15,.1);red.transparency=.1;node.addChild(red);rc=coin.SoCoordinate3();rc.point.setValues(0,len(rp),[tuple(pose.multVec(v)) for v in rp]);node.addChild(rc);ri=coin.SoIndexedFaceSet();ridx=[i for f in rf for i in (*f,-1)];ri.coordIndex.setValues(0,len(ridx),ridx);node.addChild(ri);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(mesh));self.ok.setEnabled(True);self.status.setText(tr('面数: %d → %d ／ 成分数: %d → %d','Facets: %d → %d / Components: %d → %d')%(self.source.Mesh.CountFacets,mesh.CountFacets,self.source.Mesh.copy().countComponents(),mesh.countComponents()))
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
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshDeleteDialog(ws,source).exec_()
