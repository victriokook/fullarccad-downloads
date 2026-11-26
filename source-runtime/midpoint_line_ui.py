import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_midpoint_line as backend

class MidpointLineDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main);self.ws=ws;self.sketch=ws.current_sketch();self.doc=backend.validate(self.sketch);self.stamp=backend.signature(self.sketch);self.scene=Gui.activeDocument().activeView().getSceneGraph();self.overlay=None;self.validated=None
        self.setObjectName('FullArcMidpointLine');self.setWindowTitle(tr('中点から線分','Midpoint Line'));form=W.QFormLayout(self);self.fields=[]
        for label,lo,hi,value in [(tr('中点 X','Midpoint X'),-1e6,1e6,0),(tr('中点 Y','Midpoint Y'),-1e6,1e6,0),(tr('全長','Total length'),.001,1e6,20),(tr('角度','Angle'),-360,360,0)]:
            field=W.QDoubleSpinBox();field.setDecimals(8);field.setRange(lo,hi);field.setValue(value);field.setSuffix(' °' if len(self.fields)==3 else ' mm');self.fields.append(field);form.addRow(label,field);field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.construction=W.QCheckBox(tr('補助図形','Construction geometry'));form.addRow(self.construction);self.construction.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('2Dスケッチ内の中点・全長・角度から対称な両端を作ります。角度はスケッチX軸から反時計回り。座標と両端各±1000000mm、全長0.001～1000000mm。追加後は標準線分です。中点の永続拘束・自動水平垂直拘束・スナップ・カーソル作図・専用再編集・3D線分はありません。','Creates symmetric endpoints from a 2D sketch-local midpoint,total length and angle counterclockwise from sketch X. Coordinates/endpoints each ±1000000mm;length0.001–1000000mm. Result is a standard editable line. No persistent midpoint constraint,automatic horizontal/vertical constraints,snaps,cursor drawing,dedicated re-editing or 3D line.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button);self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()
    def values(self):return (tuple(f.value() for f in self.fields[:2]),self.fields[2].value(),self.fields[3].value())
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
            self.guard();geometry=backend.curve(*self.values());points=[tuple(self.sketch.getGlobalPlacement().multVec(v)) for v in (geometry.StartPoint,geometry.EndPoint)]
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick);color=coin.SoBaseColor();color.rgb=(1,.65,.1);node.addChild(color);coords=coin.SoCoordinate3();coords.point.setValues(0,2,points);node.addChild(coords);line=coin.SoLineSet();line.numVertices.setValue(2);node.addChild(line);self.scene.addChild(node);self.overlay=node;self.validated=(self.values(),self.construction.isChecked());self.ok.setEnabled(True);self.status.setText(tr('全長 %.12g mm','Total length %.12g mm')%self.values()[1])
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
    ws.select_sketch_geometry();result=MidpointLineDialog(ws).exec_();ws.refresh();return result
