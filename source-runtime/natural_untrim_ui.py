"""Same-source face selection, transient boundary preview and guarded native copy."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_natural_untrim as backend

class NaturalUntrimDialog(W.QDialog):
    def __init__(self,ws,source,names,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=source.Document;self.source=source;self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxNaturalUntrim');self.setWindowTitle(tr('面の自然境界を復元','Restore Natural Surface Boundary'));layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('非周期のBSpline・Bezier面を1枚、Face1の形式で指定します。内外のトリムを全て外し、元の有限な自然境界まで戻します。外挿・周期面・解析面は対象外です。原本を保持して非表示にします。プレビューは輪郭線です。','Enter one nonperiodic BSpline/Bezier face as Face1. Removes all internal/external trims to its finite natural domain. No extrapolation,periodic or analytic surfaces. Retains and hides the source. Preview shows boundaries.'));note.setWordWrap(True);layout.addWidget(note);layout.addWidget(W.QLabel(source.Label));self.faces=W.QLineEdit(','.join(names));layout.addWidget(self.faces);self.faces.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button);self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False);self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def names(self):return [name.strip() for name in self.faces.text().split(',')]
    def stamp(self):
        backend.checked(self.doc,self.source,self.names(),self.existing)
        return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(o.Name for o in backend.containers(self.source)),tuple(self.names()),(tuple(self.existing.FaceNames),tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
    def invalidate(self,*args):
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError('Return to the original document.')
            shape=backend.preview(self.doc,self.source,self.names(),self.existing);node=coin.SoSeparator();color=coin.SoBaseColor();color.rgb=(1.,.55,.1);node.addChild(color)
            for edge in shape.Edges:
                points=edge.discretize(Number=65);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(v) for v in points]);node.addChild(coords);line=coin.SoLineSet();line.numVertices=len(points);node.addChild(line)
            self.scene=Gui.activeDocument().activeView().getSceneGraph();self.scene.addChild(node);self.overlay=node;self.loaded=self.stamp();self.ok.setEnabled(True);self.status.setText(tr('面積: ','Area: ')+('%.9g mm²'%shape.Area))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def guard(self):
        if App.ActiveDocument!=self.doc or self.loaded is None or self.loaded!=self.stamp():raise ValueError(tr('入力が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def refresh(self):
        if self.loaded is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:self.guard();self.invalidate();self.result_object=backend.apply(self.doc,self.source,self.names(),self.existing);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(v,'active',False) is True for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx();existing=None
    if len(selected)!=1:raise ValueError(tr('同じ原本の面を選択してください。','Select faces on one source.'))
    item=selected[0]
    if getattr(item.Object,'FluxNaturalUntrim',False) and not item.SubElementNames:existing=item.Object;source=existing.Source;names=list(existing.FaceNames)
    else:source=item.Object;names=list(item.SubElementNames)
    if existing:
        if source is None or source.Document!=App.ActiveDocument:raise ValueError('The source is missing.')
    else:backend.preview(App.ActiveDocument,source,names)
    ws.region_picker.ticket+=1;ws.region_picker.clear();return NaturalUntrimDialog(ws,source,names,existing).exec_()
