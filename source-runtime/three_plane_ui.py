"""Two explicit edge references, transient point preview and linked editing."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_three_plane_point as backend

class ThreePlaneDialog(W.QDialog):
    def __init__(self,ws,a,b,c,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=a[0].Document;self.sources=(a[0],b[0],c[0]);self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxThreePlanePoint');self.setWindowTitle(tr('3平面を通る構築点','Point Through Three Planes'));layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('3つの平面の延長交点を参照します。退化・近平行・曲面は対象外です。交点座標は各軸±1,000,000mm以内です。原本を保持し、同じ原本の面を選び直して編集できます。','Reference the extended intersection of three planar faces. Degenerate,near-parallel and curved surfaces are excluded. Each coordinate must be within±1,000,000mm. Retains sources; edit face choices on the same sources.'));note.setWordWrap(True);layout.addWidget(note);self.fields=[]
        for source,name,kind in ((a[0],a[1],'Face'),(b[0],b[1],'Face'),(c[0],c[1],'Face')):
            layout.addWidget(W.QLabel(source.Label));field=W.QComboBox();field.addItems([kind+str(i+1) for i in range(len(source.Shape.Edges if kind=='Edge' else source.Shape.Faces))]);field.setCurrentText(name);field.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));layout.addWidget(field);self.fields.append(field)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button);self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False);self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def refs(self):return tuple((source,field.currentText()) for source,field in zip(self.sources,self.fields))
    def stamp(self):
        backend.checked(self.doc,*self.refs(),self.existing)
        return tuple((fingerprint(s),tuple(s.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(s)),name) for s,name in self.refs()),(self.existing.FaceA,self.existing.FaceB,self.existing.FaceC,tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
    def invalidate(self,*args):
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            out=backend.preview(self.doc,*self.refs(),self.existing);point=out.Point;node=coin.SoSeparator();style=coin.SoDrawStyle();style.pointSize=10;node.addChild(style);color=coin.SoBaseColor();color.rgb=(1.,.55,.1);node.addChild(color);coords=coin.SoCoordinate3();coords.point.setValue(tuple(point));node.addChild(coords);marker=coin.SoPointSet();marker.numPoints=1;node.addChild(marker);self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.loaded=self.stamp();self.ok.setEnabled(True);self.status.setText('X %.9g / Y %.9g / Z %.9g mm'%(point.x,point.y,point.z))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def guard(self):
        if App.ActiveDocument!=self.doc or self.loaded is None or self.loaded!=self.stamp():raise ValueError(tr('入力が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def refresh(self):
        if self.loaded is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:self.guard();self.invalidate();self.result_object=backend.apply(self.doc,*self.refs(),self.existing);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx();existing=None;refs=[]
    if len(selected)==1 and getattr(selected[0].Object,'FluxThreePlanePoint',False) and not selected[0].SubElementNames:
        existing=selected[0].Object;refs=[(existing.SourceA,existing.FaceA),(existing.SourceB,existing.FaceB),(existing.SourceC,existing.FaceC)]
    else:
        for item in selected:
            for name in item.SubElementNames:refs.append((item.Object,name))
    if len(refs)!=3 or any(not ref[1].startswith('Face') for ref in refs):raise ValueError(tr('平面Faceを3つ選択してください。','Select three planar faces.'))
    if existing:backend.checked(App.ActiveDocument,*refs,existing)
    else:backend.preview(App.ActiveDocument,*refs)
    ws.region_picker.ticket+=1;ws.region_picker.clear();return ThreePlaneDialog(ws,*refs,existing).exec_()
