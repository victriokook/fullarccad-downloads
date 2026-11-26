import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import elliptical_arc_geometry as backend


class EllipticalArcDialog(W.QDialog):
    def __init__(self,ws,sketch):
        super().__init__(ws.main);self.ws,self.sketch,self.doc=ws,sketch,sketch.Document
        self.stamp=backend.signature(sketch);self.overlay=None;self.validated=None
        self.scene=Gui.activeDocument().activeView().getSceneGraph()
        self.setObjectName('FluxEllipticalArc');self.setWindowTitle(tr('楕円弧','Elliptical Arc'));self.setMinimumWidth(460)
        form=W.QFormLayout(self);self.fields=[]
        for key,label,low,high,value in [('CX',tr('中心X','Center X'),-1e6,1e6,0),('CY',tr('中心Y','Center Y'),-1e6,1e6,0),('Major',tr('長半径','Major radius'),.001,100000,10),('Minor',tr('短半径','Minor radius'),.001,100000,5),('Rotation',tr('長軸の回転角','Major-axis rotation'),-360,360,0),('Start',tr('開始パラメータ角','Start parameter angle'),-360,360,0),('Sweep',tr('区間パラメータ角','Sweep parameter angle'),.001,359.999,90)]:
            field=W.QDoubleSpinBox();field.setObjectName('FluxEllipticalArc'+key);field.setDecimals(8);field.setRange(low,high);field.setValue(value);field.setSuffix(' mm' if len(self.fields)<4 else ' °');form.addRow(label,field);self.fields.append(field);field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.construction=W.QCheckBox(tr('補助図形','Construction geometry'));form.addRow(self.construction);self.construction.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('座標・回転はスケッチ平面内です。長短半径の差は1e-6mm超が必要です。角度は楕円のパラメータ（x=a cos t,y=b sin t）で、極角・弧長比ではありません。長軸から反時計回りに0.001～359.999°の区間を作ります。全楕円・自動内部補助線・自動拘束・専用再編集・カーソル入力は対象外です。',
            'Coordinates/rotation are sketch-local. Major-minus-minor radius must exceed1e-6mm. Angles are ellipse parameters(x=a cos t,y=b sin t),not polar angles or arc-length fractions. Creates a counterclockwise0.001–359.999° interval from the major axis. No full ellipse,automatic internal geometry/constraints,dedicated re-editing or cursor input.'))
        note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(200);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def values(self):return tuple(f.value() for f in self.fields)+(self.construction.isChecked(),)

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.sketch.Name) is not self.sketch or self.ws.current_sketch() is not self.sketch or backend.signature(self.sketch)!=self.stamp:
            raise ValueError(tr('スケッチが変わりました。開き直してください。','The sketch changed. Reopen this dialog.'))

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
            self.guard();geometry=backend.curve(*self.values()[:7]);points=[self.sketch.getGlobalPlacement().multVec(p) for p in geometry.toShape().discretize(Number=129)]
            node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
            color=coin.SoBaseColor();color.rgb=(1.,.65,.1);node.addChild(color)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(p) for p in points]);node.addChild(coords)
            line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line)
            self.scene.addChild(node);self.overlay=node;self.validated=self.values();self.ok.setEnabled(True)
            self.status.setText(tr('プレビューを表示しました。','Preview displayed.'))
        except Exception as error:self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated!=self.values():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.result_index=backend.add(self.sketch,*self.values()[:7],construction=self.values()[7]);super().accept()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def done(self,result):self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    sketch=ws.current_sketch()
    if sketch is None or App.ActiveDocument is not sketch.Document or W.QApplication.activeModalWidget():
        raise ValueError(tr('先にスケッチの編集を開始してください。','Start sketch editing first.'))
    ws.select_sketch_geometry();dialog=EllipticalArcDialog(ws,sketch)
    result=dialog.exec_();ws.refresh();return result
