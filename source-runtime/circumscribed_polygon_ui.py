import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_circumscribed_polygon as backend

class CircumscribedPolygonDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main);self.ws=ws;self.sketch=ws.current_sketch();self.doc=backend.validate(self.sketch);self.stamp=backend.signature(self.sketch);self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FullArcCircumscribedPolygon');self.setWindowTitle(tr('外接ポリゴン','Circumscribed Polygon'));form=W.QFormLayout(self);self.fields=[]
        for label,lo,hi,value in [(tr('中心 X','Center X'),-1e6,1e6,0),(tr('中心 Y','Center Y'),-1e6,1e6,0),(tr('中心から辺までの距離','Center-to-edge distance'),.001,100000,10),(tr('角度','Angle'),-360,360,0)]:
            field=W.QDoubleSpinBox();field.setDecimals(8);field.setRange(lo,hi);field.setValue(value);field.setSuffix(' °' if len(self.fields)==3 else ' mm');self.fields.append(field);form.addRow(label,field);field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.sides=W.QSpinBox();self.sides.setRange(3,50);self.sides.setValue(6);form.addRow(tr('辺数','Sides'),self.sides);self.sides.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.construction=W.QCheckBox(tr('補助図形','Construction geometry'));form.addRow(self.construction);self.construction.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('中心から辺までの距離で正多角形を作ります。角度は中心から最初の辺の中点へ向かう方向をスケッチXから反時計回りで指定。辺数3～50、距離0.001～100000mm、中心・頂点各±1000000mm。標準の接続・等辺・外接補助円上拘束を作ります。補助円は頂点を通る円で、入力距離の円ではありません。専用距離寸法・専用再編集・スナップ・カーソル作図なし。','Creates a regular polygon using center-to-edge distance. Angle points from centre toward the midpoint of the first edge,counterclockwise from sketch X. Sides3–50,distance0.001–100000mm,centre/vertices each ±1000000mm. Native coincident,equal and point-on-circumcircle constraints are added. The construction circle passes through vertices,not the input-distance incircle. No dedicated apothem dimension/re-editing,snaps or cursor drawing.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button);self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()
    def values(self):return (tuple(f.value() for f in self.fields[:2]),self.sides.value(),self.fields[2].value(),self.fields[3].value())
    def guard(self):
        backend.validate(self.sketch)
        if self.ws.current_sketch() is not self.sketch or backend.signature(self.sketch)!=self.stamp:raise ValueError(tr('スケッチが変わりました。開き直してください。','The sketch changed. Reopen this dialog.'))
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
            self.guard();backend.outline(*self.values());points=[tuple(self.sketch.getGlobalPlacement().multVec(App.Vector(*v))) for v in backend.vertices(*self.values())]
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);color=coin.SoBaseColor();color.rgb=(1,.65,.1);node.addChild(color);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),points);node.addChild(coords);line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line);self.scene.addChild(node);self.overlay=node;self.validated=(self.values(),self.construction.isChecked());self.ok.setEnabled(True);self.status.setText(tr('中心から辺まで %.12g mm','Center-to-edge %.12g mm')%self.values()[2])
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated!=(self.values(),self.construction.isChecked()):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_index=backend.add(self.sketch,*self.values(),construction=self.construction.isChecked());super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if ws.current_sketch() is None or W.QApplication.activeModalWidget():raise ValueError(tr('先にスケッチの編集を開始してください。','Start sketch editing first.'))
    ws.select_sketch_geometry();result=CircumscribedPolygonDialog(ws).exec_();ws.refresh();return result
