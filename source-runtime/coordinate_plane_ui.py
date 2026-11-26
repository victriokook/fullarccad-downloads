import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from extrude_panel import ExtrudePanel
import model_coordinate_plane as backend

class CoordinatePlaneDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main);self.ws,self.doc=ws,App.ActiveDocument;self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FullArcCoordinatePlane');self.setWindowTitle(tr('座標と法線で平面','Plane by Coordinates and Normal'));form=W.QFormLayout(self);self.fields=[]
        for index,name in enumerate(('X','Y','Z','NX','NY','NZ',tr('正方形の辺長','Square side length'))):
            field=W.QDoubleSpinBox();field.setDecimals(8);field.setRange(.001,100000) if index==6 else field.setRange(-1e6,1e6);field.setValue(80 if index==6 else 1 if index==5 else 0);self.fields.append(field);form.addRow(name,field);field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('中心XYZと法線NX/NY/NZから独立した有限の正方形平面を作成します。座標・法線成分各±1000000、辺長0.001～100000mm、全頂点も範囲内。ブラウザーのサーフェスに保存されます。Face1を明示選択してスケッチ支持・面参照に使用できます。専用再編集・式・スナップ・原本リンクなし。面内軸は決定規則で選び、法線の変更で向きが切り替わる場合があります。Fusion setByPlaneは直接編集限定であり、無限平面・履歴・面内軸の同等性は主張しません。',
            'Creates an independent finite square plane from world centre XYZ and normal NX/NY/NZ. Each coordinate/normal component ±1000000;side0.001–100000mm;all corners also within bounds. Stored in browser Surfaces. Explicitly select Face1 for sketch support or face references. No dedicated re-editing,expressions,snaps or source link. Deterministic in-plane axes may switch as the normal changes. Fusion setByPlane is direct-edit-only;no infinite-plane,history or in-plane-frame equivalence claimed.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button);self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):
        values=[f.value() for f in self.fields];return tuple(values[:3]),tuple(values[3:6]),values[6]
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
            self.guard();xyz=self.values();backend.preview(self.doc,*xyz);points=backend.corners(*xyz)
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);material=coin.SoBaseColor();material.rgb=(.9,.5,.15);node.addChild(material);style=coin.SoDrawStyle();style.lineWidth=2;node.addChild(style);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),points);node.addChild(coords);lines=coin.SoLineSet();lines.numVertices.setValues(0,1,[5]);node.addChild(lines);self.scene.addChild(node);self.overlay=node;self.validated=backend.corners(*xyz);self.ok.setEnabled(True);self.status.setText(tr('正方形の辺長 %.12g mm','Square side length %.12g mm')%xyz[2])
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated is None or self.validated!=backend.corners(*self.values()):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_object=backend.create(self.doc,*self.values(),expected=self.validated);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh();super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    return CoordinatePlaneDialog(ws).exec_()
