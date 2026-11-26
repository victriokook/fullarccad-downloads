import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_reverse as backend


class MeshReverseDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshReverse');self.setWindowTitle(tr('メッシュ法線を反転','Reverse Mesh Normals'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label));note=W.QLabel(tr('メッシュ全体1～20000面の向きを反転し、頂点座標は保持します。開いた単一メッシュにも対応します。原本を保持・非表示にして独立結果を作ります。最大200面の反転後法線を矢印表示します。外向きの自動判定・修復、部分面／面グループ、追従履歴・専用再編集・面別色保持は対象外です。内向きになる場合があります。','Reverses all1–20000 mesh facets while preserving vertex coordinates;also accepts one open mesh. Retains and hides the original;creates an independent result. Preview shows up to200 post-reversal normal arrows. No automatic outward detection/repair,partial faces/face groups,linked history/dedicated re-editing or per-facet colors. The result can face inward.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.source.Name) is not self.source or self.ws.current_sketch() or backend.stamp(self.source)!=self.initial:
            raise ValueError(tr('文書またはメッシュが変わりました。開き直してください。','The document or mesh changed. Reopen this dialog.'))

    def refresh_guard(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def invalidate(self):
        if self.overlay is not None:
            try:self.scene.removeChild(self.overlay)
            except RuntimeError:pass
        self.overlay=None;self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();mesh,pose=backend.reverse(self.doc,self.source);points=backend.normal_lines(mesh,pose)
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);color=coin.SoBaseColor();color.rgb=(1.,.35,.1);node.addChild(color)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(p) for p in points]);node.addChild(coords)
            lines=coin.SoLineSet();lines.numVertices.setValues(0,len(points)//2,[2]*(len(points)//2));node.addChild(lines);self.scene.addChild(node);self.overlay=node
            self.validated=backend.fingerprint(mesh);self.ok.setEnabled(True);self.status.setText(tr('反転する面数: %d / 法線表示: %d面','Reversed facets: %d / Normals displayed: %d')%(mesh.CountFacets,len(points)//6))
        except Exception as error:self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated is None:raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_object=backend.create(self.doc,self.source,expected=self.validated);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def done(self,result):self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('メッシュ全体を1つ選択してください。','Select one whole mesh.'))
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshReverseDialog(ws,source).exec_()
