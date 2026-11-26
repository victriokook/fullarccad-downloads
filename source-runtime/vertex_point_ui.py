"""Explicit vertex point dialog with transient Coin preview."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_vertex_point as backend
from extrude_panel import ExtrudePanel

class VertexDialog(W.QDialog):
    def __init__(self,ws,source,name,existing=None):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.doc=source.Document;self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxVertexPointDialog');self.setWindowTitle(tr('頂点に構築点','Point at Vertex'))
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('対象: %s\n明示的な頂点から独立した参照点を作成します。原本は保持します。','Source: %s\nCreates an independent linked point from an explicit vertex. Retains the source.')%source.Label);note.setWordWrap(True);layout.addWidget(note)
        self.vertex=W.QComboBox();self.vertex.setObjectName('VertexPointElement');layout.addWidget(self.vertex)
        for i in range(len(source.Shape.Vertexes)):self.vertex.addItem('Vertex'+str(i+1))
        self.vertex.setCurrentText(name);self.vertex.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def stamp(self):
        backend.checked(self.doc,self.source)
        return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.containers(self.source)),getattr(self.source,'Error',''),self.vertex.currentText(),(self.existing.VertexName,tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
    def invalidate(self,*args):
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            out=backend.preview(self.doc,self.source,self.vertex.currentText(),self.existing);point=out.Point
            node=coin.SoSeparator();style=coin.SoDrawStyle();style.pointSize=10;node.addChild(style);color=coin.SoBaseColor();color.rgb=(1.,.55,.1);node.addChild(color);coords=coin.SoCoordinate3();coords.point.setValue(tuple(point));node.addChild(coords);marker=coin.SoPointSet();marker.numPoints=1;node.addChild(marker)
            self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.loaded=self.stamp();self.preview_point=point;self.ok.setEnabled(True);self.status.setText('X %.9g / Y %.9g / Z %.9g mm'%(point.x,point.y,point.z))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def guard(self):
        if App.ActiveDocument!=self.doc or self.loaded is None or self.loaded!=self.stamp():raise ValueError(tr('入力が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def refresh(self):
        if self.loaded is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard();self.invalidate();self.result_object=backend.apply(self.doc,self.source,self.vertex.currentText(),self.existing);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1:raise ValueError(tr('頂点を1つ選択してください。','Select one vertex.'))
    item=selected[0];obj=item.Object
    if getattr(obj,'FluxVertexPoint',False) and not item.SubElementNames:source=obj.Source;name=obj.VertexName;existing=obj
    else:
        source=obj;existing=None
        if len(item.SubElementNames)!=1:raise ValueError(tr('明示的なVertex要素を1つ選択してください。','Select one explicit Vertex element.'))
        name=item.SubElementNames[0]
    backend.checked(source.Document,source,existing)
    if existing:
        if not source.Shape.Vertexes:raise ValueError(tr('参照元に頂点がありません。','The source has no vertices.'))
        if name not in ['Vertex'+str(i+1) for i in range(len(source.Shape.Vertexes))]:name='Vertex1'
    else:backend.preview(source.Document,source,name)
    ws.region_picker.ticket+=1;ws.region_picker.clear()
    return VertexDialog(ws,source,name,existing).exec()
