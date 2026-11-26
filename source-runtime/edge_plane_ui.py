"""Two explicit edge references, transient point preview and linked editing."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_edge_plane_point as backend

class EdgePlaneDialog(W.QDialog):
    def __init__(self,ws,a,b,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=a[0].Document;self.sources=(a[0],b[0]);self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxEdgePlanePoint');self.setWindowTitle(tr('辺と平面の交点に構築点','Point At Edge And Plane'));layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('直線辺と平面の延長交点を参照します。近平行・曲線・曲面は対象外です。交点座標は各軸±1,000,000mm以内です。原本を保持し、同じ原本の辺と面を選び直して編集できます。','Reference the extended intersection of a straight edge and planar face. Near-parallel lines,curves and curved surfaces are excluded. Each coordinate must be within±1,000,000mm. Retains sources; edit edge and face choices on the same sources.'));note.setWordWrap(True);layout.addWidget(note);self.fields=[]
        for source,name,kind in ((a[0],a[1],'Edge'),(b[0],b[1],'Face')):
            layout.addWidget(W.QLabel(source.Label));field=W.QComboBox();field.addItems([kind+str(i+1) for i in range(len(source.Shape.Edges if kind=='Edge' else source.Shape.Faces))]);field.setCurrentText(name);field.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));layout.addWidget(field);self.fields.append(field)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button);self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False);self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def refs(self):return tuple((source,field.currentText()) for source,field in zip(self.sources,self.fields))
    def stamp(self):
        backend.checked(self.doc,*self.refs(),self.existing)
        return tuple((fingerprint(s),tuple(s.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(s)),name) for s,name in self.refs()),(self.existing.EdgeA,self.existing.FaceB,tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
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
    if len(selected)==1 and getattr(selected[0].Object,'FluxEdgePlanePoint',False) and not selected[0].SubElementNames:
        existing=selected[0].Object;refs=[(existing.SourceA,existing.EdgeA),(existing.SourceB,existing.FaceB)]
    else:
        for item in selected:
            for name in item.SubElementNames:refs.append((item.Object,name))
    if len(refs)!=2:raise ValueError(tr('直線辺と平面を1つずつ選択してください。','Select one straight edge and one planar face.'))
    if existing is None:
        edges=[ref for ref in refs if ref[1].startswith('Edge')];faces=[ref for ref in refs if ref[1].startswith('Face')]
        if len(edges)!=1 or len(faces)!=1:raise ValueError('Select one Edge and one Face.')
        refs=edges+faces
    if existing:backend.checked(App.ActiveDocument,*refs,existing)
    else:backend.preview(App.ActiveDocument,*refs)
    ws.region_picker.ticket+=1;ws.region_picker.clear();return EdgePlaneDialog(ws,*refs,existing).exec_()
