import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_mesh_merge as backend

class MeshMergeDialog(W.QDialog):
    def __init__(self,ws,sources):
        super().__init__(ws.main);self.ws,self.sources,self.doc=ws,tuple(sources),sources[0].Document;self.initial=backend.stamp(self.sources)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxMeshMerge');self.setWindowTitle(tr('メッシュを統合','Merge Meshes'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Sources'),W.QLabel(', '.join(s.Label for s in self.sources)))
        note=W.QLabel(tr('メッシュ全体2～20個、合計1～20000面を1つの独立メッシュに統合します。開いた面・離れた成分・重複／内部面・向きを保持します。原本は全て保持・非表示にします。Boolean和差積、境界の縫合、修復、外向き保証、追従履歴・専用再編集・個別色の保持は対象外です。色は先頭原本を使います。世界座標への変換にはnativeメッシュの単精度丸めが入ります。','Combines2–20 whole meshes with up to20000 total facets into one independent mesh. Preserves open surfaces,separate components,overlapping/internal faces and orientation. Retains and hides all originals. No Boolean union/cut/intersection,boundary stitching,repair,outward guarantee,linked history/dedicated re-editing or individual color preservation. Uses the first source color. Native single-precision rounding applies when baking world coordinates.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()
    def guard(self):
        if App.ActiveDocument is not self.doc or self.ws.current_sketch() or any(self.doc.getObject(s.Name) is not s for s in self.sources) or backend.stamp(self.sources)!=self.initial:raise ValueError(tr('文書または原本が変わりました。開き直してください。','The document or sources changed. Reopen this dialog.'))
    def refresh_guard(self):
        try:self.guard()
        except Exception as e:self.invalidate();self.status.setText(str(e))
    def invalidate(self):
        if self.overlay is not None:
            try:self.scene.removeChild(self.overlay)
            except RuntimeError:pass
        self.overlay=None;self.validated=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();mesh,pose=backend.merge(self.doc,self.sources);points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(p) for p in points]);node.addChild(coords);faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);self.scene.addChild(node);self.overlay=node
            self.validated=backend.fingerprint(mesh);self.ok.setEnabled(True);self.status.setText(tr('原本: %d個 → 1個 / 面数: %d','Sources: %d → 1 / Facets: %d')%(len(self.sources),mesh.CountFacets))
        except Exception as e:self.status.setText(str(e))
    def accept(self):
        try:
            self.guard()
            if self.validated is None:raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_object=backend.create(self.doc,self.sources,expected=self.validated);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as e:self.invalidate();self.status.setText(str(e))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx()
    if not 2<=len(selected)<=20 or any(s.SubElementNames for s in selected):raise ValueError(tr('メッシュ全体を2～20個選択してください。','Select2–20 whole meshes.'))
    sources=tuple(s.Object for s in selected);backend.validate(App.ActiveDocument,sources);return MeshMergeDialog(ws,sources).exec_()
