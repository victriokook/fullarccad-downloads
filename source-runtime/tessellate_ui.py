import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_tessellate as backend


class TessellateDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source)
        self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxTessellate');self.setWindowTitle(tr('CAD形状からメッシュを作成','Create Mesh from CAD'));form=W.QFormLayout(self)
        form.addRow(tr('原本','Source'),W.QLabel(source.Label));self.linear=W.QDoubleSpinBox();self.linear.setDecimals(8);self.linear.setRange(.01,1000);self.linear.setValue(backend.defaults(self.doc,source)[0]);self.linear.setSuffix(' mm')
        self.angle=W.QDoubleSpinBox();self.angle.setDecimals(8);self.angle.setRange(5,90);self.angle.setValue(20);self.angle.setSuffix(' °')
        form.addRow(tr('表面偏差（native設定）','Surface deflection (native)'),self.linear);form.addRow(tr('角度偏差（native設定）','Angular deflection (native)'),self.angle)
        note=W.QLabel(tr('単一ソリッドまたは開いたFace/Shell全体（1～200面）から、独立した標準メッシュを作成します。表面偏差.01～1000mm、角度偏差5～90°、対角長10000mm以下・偏差は対角長/2000以上、出力1～20000三角形です。原本は保持・非表示にし、親配置を含め一度だけ配置します。nativeの近似設定であり、全表面偏差やFusionの設定との同等性を保証しません。四角形・面グループ・色分け・最大辺長・縦横比・追従履歴・専用再編集は対象外です。','Creates an independent standard mesh from one whole Solid or open Face/Shell with1–200 CAD faces. Linear deflection .01–1000mm,angular5–90°,diagonal<=10000mm,linear>=diagonal/2000;output1–20000 triangles. Retains and hides the original;applies full parent/own placement once. Native approximation parameters do not certify global deviation or equivalence to Fusion settings. No quads,face groups,per-face colors,max-edge/aspect controls,linked history or dedicated re-editing.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.linear.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.angle.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return self.linear.value(),self.angle.value()

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.source.Name) is not self.source or self.ws.current_sketch() or backend.stamp(self.source)!=self.initial:
            raise ValueError(tr('文書またはCAD形状が変わりました。開き直してください。','The document or CAD shape changed. Reopen this dialog.'))

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
            self.guard();mesh,pose=backend.tessellate(self.doc,self.source,*self.values());points,facets=mesh.Topology
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);material.transparency=.35;node.addChild(material)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(pose.multVec(p)) for p in points]);node.addChild(coords)
            faces=coin.SoIndexedFaceSet();indices=[i for f in facets for i in (*f,-1)];faces.coordIndex.setValues(0,len(indices),indices);node.addChild(faces);self.scene.addChild(node);self.overlay=node
            self.validated=(self.values(),backend.fingerprint(mesh));self.ok.setEnabled(True);self.status.setText(tr('生成する三角形数: %d','Triangles to create: %d')%mesh.CountFacets)
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
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('CAD形状全体を1つ選択してください。','Select one whole CAD shape.'))
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return TessellateDialog(ws,source).exec_()
