from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from i18n import tr
from extrude_panel import ExtrudePanel
import model_tapered_extrude as backend

class TaperedExtrudeDialog(W.QDialog):
    def __init__(self,ws,source,existing=None):
        super().__init__(ws.main)
        self.ws,self.source,self.existing,self.doc=ws,source,existing,App.ActiveDocument
        self.initial_stamp=backend.stamp(source,existing)
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.setObjectName('FluxTaperedExtrude');self.setWindowTitle(tr('テーパー押し出し','Tapered Extrude'))
        form=W.QFormLayout(self);form.addRow(tr('原本','Source'),W.QLabel(source.Label))
        self.extent_mode=W.QComboBox()
        for label,key in [(tr('片側／両側を個別指定','Separate Sides'),'sides'),(tr('対称・片側長','Symmetric Half Length'),'symmetric_half'),(tr('対称・全長','Symmetric Whole Length'),'symmetric_whole')]:self.extent_mode.addItem(label,key)
        self.extent_mode.setCurrentIndex(self.extent_mode.findData(getattr(existing.Input,'ExtentMode','sides') if existing else 'sides'));form.addRow(tr('押し出し範囲','Extent'),self.extent_mode)
        self.height=W.QDoubleSpinBox();self.angle=W.QDoubleSpinBox();self.reverse=W.QCheckBox(tr('方向を反転','Reverse direction'))
        self.height.setDecimals(8);self.height.setRange(.001,100000);self.height.setSuffix(' mm')
        self.angle.setDecimals(8);self.angle.setRange(-45,45);self.angle.setSuffix('°')
        self.original=(existing.Input.Height,existing.Input.TaperAngle) if existing else (10.,5.)
        self.height.setValue(self.original[0]);self.angle.setValue(self.original[1]);self.display=(self.height.value(),self.angle.value());self.reverse.setChecked(bool(existing.Input.Reverse) if existing else False)
        form.addRow(tr('高さ','Height'),self.height);form.addRow(tr('テーパー角度','Taper angle'),self.angle);form.addRow(self.reverse)
        self.start_offset=W.QDoubleSpinBox();self.start_offset.setDecimals(8);self.start_offset.setRange(-100000,100000);self.start_offset.setSuffix(' mm')
        self.original_offset=getattr(existing.Input,'StartOffset',0.) if existing else 0.;self.start_offset.setValue(self.original_offset);self.display_offset=self.start_offset.value()
        form.addRow(tr('開始オフセット','Start Offset'),self.start_offset)
        expressions=[(key,value) for key,value in existing.Input.ExpressionEngine if key.lstrip('.')=='StartOffset'] if existing else []
        if expressions:self.start_offset.setEnabled(False);self.start_offset.setToolTip(tr('式で指定されています。参照元の式を編集してください。','Controlled by an expression. Edit the source expression.'))
        self.start_offset.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.height2=W.QDoubleSpinBox();self.angle2=W.QDoubleSpinBox();self.height2.setDecimals(8);self.height2.setRange(0,100000);self.height2.setSuffix(' mm');self.angle2.setDecimals(8);self.angle2.setRange(-45,45);self.angle2.setSuffix('°')
        self.original2=(getattr(existing.Input,'SecondHeight',0.),getattr(existing.Input,'SecondAngle',0.)) if existing else (0.,0.)
        self.height2.setValue(self.original2[0]);self.angle2.setValue(self.original2[1]);self.display2=(self.height2.value(),self.angle2.value());self.angle2.setEnabled(self.height2.value()>0)
        form.addRow(tr('反対側の高さ（0で片側）','Opposite Height (0 for One Side)'),self.height2);form.addRow(tr('反対側のテーパー角度','Opposite Taper Angle'),self.angle2)
        self.extent_mode.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.mode_changed))
        self.mode_changed()
        self.height2.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.second_changed));self.angle2.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))

        note=W.QLabel(tr('穴50個以下の単一平面領域（全体が1面または閉じたワイヤ群）を新規ボディに押し出します。直線・円弧のみ、合計200辺以下。正角度で外周が広がり、穴は狭まります。端面で穴が消える入力は拒否します。反対側は0で片側、0.001～100000mmで両側を別々に指定できます。対称は片側長または全長を指定し、両側に同じ角度を適用します。対称の全長は最大100000mmです。開始オフセット±100000mmは原本平面の法線方向を基準にし、方向反転とは独立です。ソリッドの部分面・結合・切取りは対象外です。','Extrudes one whole planar region with up to50 holes, from a face or closed wires into a new body. At most200 straight/circular edges. Positive taper expands the exterior and narrows holes. A hole disappearing at either end cap is rejected. Opposite height0 keeps one side;0.001–100000mm enables separate extents and taper on both sides. Symmetric uses half or whole length with equal taper on both sides; total symmetric length is at most100000mm. Start offset +/-100000mm follows the source profile normal independently of Reverse. Solid subfaces, joining and cutting are excluded.'));note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.height.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.angle.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
    def mode_changed(self,*args):
        separate=self.extent_mode.currentData()=='sides'
        if not separate:self.height2.setValue(0);self.angle2.setValue(0)
        self.height2.setEnabled(separate);self.angle2.setEnabled(separate and self.height2.value()>0)
        if hasattr(self,'ok'):self.invalidate()
    def second_changed(self,*args):
        if self.height2.value()==0:self.angle2.setValue(0)
        self.angle2.setEnabled(self.height2.value()>0);self.invalidate()
    def second_values(self):
        values=[old if field.value()==shown else field.value() for field,old,shown in zip((self.height2,self.angle2),self.original2,self.display2)]
        return dict(second_height=values[0],second_angle=values[1],extent_mode=self.extent_mode.currentData(),start_offset=self.original_offset if self.start_offset.value()==self.display_offset else self.start_offset.value())
    def values(self):
        return (*[old if field.value()==shown else field.value() for field,old,shown in zip((self.height,self.angle),self.original,self.display)],self.reverse.isChecked())
    def guard(self):
        if App.ActiveDocument is not self.doc or self.ws.current_sketch() or self.doc.getObject(self.source.Name) is not self.source or (self.existing and self.doc.getObject(self.existing.Name) is not self.existing) or backend.stamp(self.source,self.existing)!=self.initial_stamp:
            raise ValueError(tr('文書または対象が変わりました。開き直してください。','The document or target changed. Reopen this dialog.'))
    def invalidate(self,*_):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.doc,self.source,*self.values(),existing=self.existing,**self.second_values())
            ExtrudePanel.show_shape(self.host,shape,'new')
            if self.existing:self.host.hidden.append((self.existing,bool(self.existing.Visibility)));self.existing.Visibility=False
            self.validated=(self.values(),self.second_values());self.ok.setEnabled(True);self.status.setText(tr('体積: %.6g mm³','Volume: %.6g mm³')%shape.Volume)
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated!=(self.values(),self.second_values()):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.apply(self.doc,self.source,*self.values(),existing=self.existing,**self.second_values())
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('文書を開き、現在の編集を終了してください。','Open a document and finish the current edit.'))
    selected=Gui.Selection.getSelection()
    if len(selected)!=1:raise ValueError(tr('平面輪郭を1つ選択してください。','Select one planar profile.'))
    existing=selected[0] if getattr(selected[0],'FluxTaperedExtrude',False) else None
    source=existing.Source if existing else selected[0];backend.validate(App.ActiveDocument,source,existing);backend.checked_source(source)
    return TaperedExtrudeDialog(ws,source,existing).exec_()
