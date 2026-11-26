"""Whole-curve projection dialog; explicit all-intersections output."""
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
from model_defeature import fingerprint
import model_isocurve as backend
from single_face_ui import is_single_face

class IsoDialog(W.QDialog):
    def __init__(self,ws,source=None,existing=None):
        super().__init__(ws.main);self.ws=ws;self.doc=App.ActiveDocument;self.existing=existing
        self.setObjectName('FluxIsoCurveDialog');self.setWindowTitle(tr('等パラメータ曲線を抽出','Extract Isoparametric Curve'))
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('平面・円柱・球・トーラス・円すい・Bスプライン・ベジェの単一面からU/V等パラメータ線を抽出します。比率はUV範囲の0.001～0.999で、弧長比率ではありません。面の外周・穴で切り詰め、すべての線分を保持します。本数1では指定比率、2～50本では境界を除く i/(本数+1) のUV比率に配置します。両方向では各方向に指定本数を作ります。追従をオフにすると独立した曲線を新規作成します。独立曲線はこのダイアログでは再編集できません。自由曲面は各方向の制御点2～50、次数1～9が対象です。スケッチ取込み・その他の曲面は対象外です。','Extract U/V isoparametric curves from one planar, cylindrical, spherical, toroidal, conical, BSpline or Bezier face. Fraction0.001–0.999 uses the UV range, not arc length. Clips at face boundaries and holes and keeps every segment. Count1 uses the specified fraction; count2–50 uses evenly spaced UV fractions i/(count+1), excluding boundaries. Both creates this count per direction. Uncheck Follow Source Changes to create independent curves; these cannot be re-edited with this dialog. Freeform surfaces require2–50 poles and degree1–9 per direction. No sketch inclusion or other surface types.'));note.setWordWrap(True);layout.addWidget(note)
        form=W.QFormLayout();layout.addLayout(form);self.source=W.QComboBox();form.addRow(tr('入力面','Input Face'),self.source)
        for obj in self.doc.Objects:
            if obj==existing or not hasattr(obj,'Shape') or obj.Shape.isNull():continue
            if existing and existing in obj.OutListRecursive:continue
            if is_single_face(obj.Shape):self.source.addItem(obj.Label,obj.Name)
        if source:self.source.setCurrentIndex(self.source.findData(source.Name))
        self.axis=W.QComboBox();self.axis.addItems(['U','V','UV']);self.axis.setCurrentText(existing.Axis if existing else 'U');form.addRow(tr('方向','Direction'),self.axis)
        self.fraction=W.QDoubleSpinBox();self.fraction.setDecimals(8);self.fraction.setRange(.001,.999);initial=existing.Fraction if existing else .5;self.fraction.setValue(initial);self.initial_fraction=(initial,self.fraction.value());form.addRow(tr('パラメータ比率','Parameter Fraction'),self.fraction)
        self.count=W.QSpinBox();self.count.setRange(1,50);self.count.setValue(getattr(existing,'Count',1) if existing else 1);form.addRow(tr('方向ごとの本数','Count per Direction'),self.count);self.fraction.setEnabled(self.count.value()==1)
        self.linked=W.QCheckBox(tr('原本の変更に追従','Follow Source Changes'));self.linked.setChecked(True);self.linked.setEnabled(existing is None);form.addRow(self.linked);self.linked.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.axis.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.fraction.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.count.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.distribution_changed))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('確定','Confirm'));self.ok.setEnabled(False)
        self.source.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def distribution_changed(self,*args):
        self.fraction.setEnabled(self.count.value()==1);self.invalidate()
    def input(self):return self.doc.getObject(self.source.currentData() or '')
    def values(self):return self.axis.currentText(),self.initial_fraction[0] if self.fraction.value()==self.initial_fraction[1] else self.fraction.value()
    def stamp(self):
        source=self.input();backend.checked(self.doc,source,self.existing)
        return (source.Name,fingerprint(source),tuple(source.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in backend.parents([source]))),(self.values(),self.count.value(),self.linked.isChecked()),(self.existing.Source.Name if self.existing.Source else None,self.existing.Axis,self.existing.Fraction,getattr(self.existing,"Count",1),self.existing.Error,fingerprint(self.existing),tuple(self.existing.getGlobalPlacement().toMatrix().A)) if self.existing else None
    def invalidate(self,*args):ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def guard(self):
        if App.ActiveDocument!=self.doc or self.validated is None or self.stamp()!=self.validated:raise ValueError(tr('対象が変わりました。再度プレビューしてください。','Inputs changed. Preview again.'))
    def preview(self):
        self.invalidate()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            source=self.input();shape=backend.preview(self.doc,source,*self.values(),existing=self.existing,count=self.count.value());self.validated=self.stamp();ExtrudePanel.show_shape(self.host,shape,'new');self.ok.setEnabled(True);self.status.setText(tr('全%d辺を保持します。','Retain all %d edges.')%len(shape.Edges))
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def refresh(self):
        if self.validated is None:return
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def accept(self):
        try:
            self.guard();source=self.input();values=self.values();self.invalidate();self.result_object=backend.apply(self.doc,source,*values,existing=self.existing,count=self.count.value(),linked=self.linked.isChecked())
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(isinstance(v,ExtrudePanel) and v.active for v in vars(ws).values()):raise ValueError(tr('開いている編集を終了してください。','Finish the current edit first.'))
    selections=Gui.Selection.getSelectionEx();existing=None;source=None
    if len(selections)>1 or any(s.SubElementNames for s in selections):raise ValueError(tr('単一面のオブジェクト全体を1つ選択してください。','Select one whole single-face object.'))
    if selections:
        obj=selections[0].Object
        if getattr(obj,'FluxIsoCurve',False):existing=obj;source=existing.Source
        elif hasattr(obj,'Shape') and is_single_face(obj.Shape):source=obj
        else:raise ValueError(tr('単一面を選択してください。','Select one single-face object.'))
    ws.region_picker.ticket+=1;ws.region_picker.clear()
    return IsoDialog(ws,source,existing).exec()
