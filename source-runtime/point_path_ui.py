"""Whole-edge point dialog with transient Coin point preview."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
from model_defeature import fingerprint
import model_point_path as backend
from extrude_panel import ExtrudePanel

class PointDialog(W.QDialog):
    def __init__(self,ws,source,existing=None):
        super().__init__(ws.main);self.ws=ws;self.source=source;self.doc=source.Document;self.existing=existing;self.overlay=None;self.scene=None;self.loaded=None
        self.setObjectName('FluxPointAlongEdge');self.setWindowTitle(tr('エッジに沿った構築点','Point Along Edge'))
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('対象: %s\n単一エッジまたは開いた／閉じた連続ワイヤ（最大200辺）の弧長で位置を指定します。割合は0～1、実距離は全長以内です。始点はワイヤの辺順序に従います。閉ワイヤの始点はネイティブの継ぎ目で、割合0と1は同じ位置です。始点の固定や選択・分離線・延長は対象外です。','Source: %s\nLocate by arc length on one whole edge or open or closed connected wire (up to 200 edges). Fraction is 0–1; distance must fit the total length. Start follows native wire order. A closed wire starts at its native seam; fractions0 and1 coincide. Custom or persistent start selection, disconnected curves and extension are excluded.')%source.Label);note.setWordWrap(True);layout.addWidget(note)
        form=W.QFormLayout();layout.addLayout(form);self.mode=W.QComboBox();self.mode.addItem(tr('割合','Fraction'),'fraction');self.mode.addItem(tr('実距離 (mm)','Distance (mm)'),'distance');self.value=W.QDoubleSpinBox();self.value.setDecimals(10);self.value.setRange(0,1e9);self.value.setValue(existing.Value if existing else .5);self.reverse=W.QCheckBox(tr('反対側から','From opposite end'));self.reverse.setChecked(existing.Reverse if existing else False)
        if existing:self.mode.setCurrentIndex(self.mode.findData(str(existing.Mode)))
        form.addRow(tr('指定方法','Position Type'),self.mode);form.addRow(tr('位置','Position'),self.value);form.addRow(self.reverse)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.original_value=existing.Value if existing else None;self.value_changed=False
        self.mode.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.value.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.mark_value));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def mark_value(self,*args):self.value_changed=True;self.invalidate()
    def inputs(self):return self.mode.currentData(),(self.original_value if self.original_value is not None and not self.value_changed else self.value.value()),self.reverse.isChecked()
    def stamp(self):
        backend.checked(self.doc,self.source,self.existing)
        return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.containers(self.source)),self.inputs(),(self.existing.Source.Name if self.existing.Source else None,str(self.existing.Mode),self.existing.Value,self.existing.Reverse,tuple(self.existing.getGlobalPlacement().toMatrix().A),self.existing.Error) if self.existing else None
    def invalidate(self,*args):
        if self.overlay is not None and self.scene is not None:self.scene.removeChild(self.overlay)
        self.overlay=None;self.scene=None;self.loaded=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            out=backend.preview(self.doc,self.source,*self.inputs(),self.existing);point=out.Point
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
            self.guard();values=self.inputs();self.invalidate();self.result_object=backend.apply(self.doc,self.source,*values,self.existing);Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('単一エッジまたはワイヤ全体を選択してください。','Select one whole edge or wire object.'))
    obj=selected[0].Object;existing=obj if getattr(obj,'FluxPointPath',False) else None;source=existing.Source if existing else obj;ws.region_picker.ticket+=1;ws.region_picker.clear()
    return PointDialog(ws,source,existing).exec()
