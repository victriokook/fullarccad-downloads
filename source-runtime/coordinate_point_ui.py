import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from extrude_panel import ExtrudePanel
import model_coordinate_point as backend

class CoordinatePointDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main);self.ws,self.doc=ws,App.ActiveDocument;self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FluxCoordinatePoint');self.setWindowTitle(tr('座標で構築点','Construction Point by Coordinates'));form=W.QFormLayout(self);self.fields=[]
        for name in ('X','Y','Z'):
            field=W.QDoubleSpinBox();field.setDecimals(8);field.setRange(-1e6,1e6);field.setSuffix(' mm');self.fields.append(field);form.addRow(name,field);field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('世界座標XYZで独立した構築点を作成します。各±1000000mm。原本や選択形状へのリンクはなく、選択形状は変更しません。移動は既存の移動操作で行えます。座標の専用再編集・追従履歴・スナップ・式入力は対象外です。FusionのPoint3D構築点は直接編集モード限定であり、パラメトリック履歴との同等性は主張しません。',
            'Creates an independent construction point at world XYZ, each ±1000000mm. No source/selection link; selected geometry is unchanged. Use existing Move operations to reposition. No dedicated coordinate re-editing, linked history, snapping or expression entry. Fusion Point3D construction points require direct edit mode; no parametric-history equivalence is claimed.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button);self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return tuple(field.value() for field in self.fields)
    def guard(self):
        backend.validate(self.doc)
        if self.ws.current_sketch():raise ValueError(tr('スケッチ編集を終了し、開き直してください。','Finish sketch editing and reopen.'))
    def invalidate(self,*_):
        if self.overlay is not None:
            try:self.scene.removeChild(self.overlay)
            except RuntimeError:pass
        self.overlay=None;self.validated=None
        if hasattr(self,'ok'):self.ok.setEnabled(False)
    def refresh_guard(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def preview(self):
        self.invalidate()
        try:
            self.guard();xyz=self.values();backend.preview(self.doc,*xyz);points=backend.preview_points(*xyz)
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);material=coin.SoBaseColor();material.rgb=(.9,.5,.15);node.addChild(material);style=coin.SoDrawStyle();style.lineWidth=2;node.addChild(style);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),points);node.addChild(coords);lines=coin.SoLineSet();lines.numVertices.setValues(0,3,[2,2,2]);node.addChild(lines);self.scene.addChild(node);self.overlay=node;self.validated=xyz;self.ok.setEnabled(True);self.status.setText('X %.12g / Y %.12g / Z %.12g mm'%xyz)
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated is None or self.validated!=self.values():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_object=backend.create(self.doc,*self.values(),expected=self.validated);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    return CoordinatePointDialog(ws).exec_()
