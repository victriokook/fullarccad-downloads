from pathlib import Path
import hashlib
from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
from extrude_panel import ExtrudePanel
from pivy import coin
import model_text_sketch as backend


class TextSketchDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main)
        self.ws,self.doc=ws,App.ActiveDocument
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None)
        self.validated=None
        self.setObjectName('FluxTextSketch');self.setWindowTitle(tr('文字をスケッチ曲線にする','Text as Sketch Curves'))
        self.setMinimumWidth(470);form=W.QFormLayout(self)
        self.text=W.QLineEdit('FluxCAD');self.text.setMaxLength(20)
        self.font=W.QLineEdit('C:/Windows/Fonts/meiryo.ttc' if Path('C:/Windows/Fonts/meiryo.ttc').is_file() else 'C:/Windows/Fonts/arial.ttf')
        row=W.QWidget();layout=W.QHBoxLayout(row);layout.setContentsMargins(0,0,0,0);layout.addWidget(self.font)
        browse=W.QPushButton(tr('参照…','Browse…'));layout.addWidget(browse)
        form.addRow(tr('文字','Text'),self.text);form.addRow(tr('フォントファイル','Font file'),row)
        self.height=W.QDoubleSpinBox();self.tracking=W.QDoubleSpinBox()
        for field,low,high,value,label in [(self.height,.1,1000,10,tr('文字高さ','Text height')),(self.tracking,-1000,1000,0,tr('字間の追加距離','Additional tracking'))]:
            field.setDecimals(8);field.setRange(low,high);field.setValue(value);field.setSuffix(' mm');form.addRow(label,field)
        note=W.QLabel(tr('日本語・英数記号1～20文字、1行、最大300曲線。新しいXY平面スケッチを作成します。曲線は独立して編集可能で、保存後はフォント不要です。文字列としての再編集・既存スケッチへの追加・自動拘束はありません。',
            'Use 1–20 Japanese/ASCII characters on one line,up to300 curves. Creates a new XY sketch with independent editable curves;the font is unnecessary after saving. No text re-editing,appending to an existing sketch or automatic constraints.'))
        note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        for field in (self.text,self.font):field.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        for field in (self.height,self.tracking):field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        browse.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.choose));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(200);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def choose(self):
        name,_=W.QFileDialog.getOpenFileName(self,tr('フォントを選択','Choose Font'),self.font.text(),'Fonts (*.ttf *.otf *.ttc)')
        if name:self.font.setText(name)

    def values(self):return self.text.text(),self.font.text(),self.height.value(),self.tracking.value()

    def font_stamp(self):
        path=Path(self.font.text())
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc is None or self.ws.current_sketch() or Gui.Control.activeDialog():
            raise ValueError(tr('文書または編集状態が変わりました。開き直してください。','The document or edit state changed. Reopen this dialog.'))

    def refresh_guard(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.status.setText(str(error))

    def invalidate(self,*_):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();shape,faces=backend.outline(*self.values());self.show_lines(shape)
            self.validated=(self.values(),self.font_stamp());self.ok.setEnabled(True)
            self.status.setText(tr('曲線数: %d / 面積: %.6g mm²','Curves: %d / Area: %.6g mm²')%(len(shape.Edges),faces.Area))
        except Exception as error:self.status.setText(str(error))

    def show_lines(self,shape):
        node=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;node.addChild(pick)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.2,.65,.9);node.addChild(material)
        style=coin.SoDrawStyle();style.lineWidth=2;node.addChild(style)
        points=[];counts=[]
        for edge in shape.Edges:
            samples=edge.discretize(Number=65);points.extend(tuple(p) for p in samples);counts.append(len(samples))
        coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),points);node.addChild(coords)
        lines=coin.SoLineSet();lines.numVertices.setValues(0,len(counts),counts);node.addChild(lines)
        graph=Gui.activeDocument().activeView().getSceneGraph();graph.addChild(node)
        self.host.overlay=(graph,node);self.host.preview_shape=shape

    def accept(self):
        try:
            self.guard()
            if self.validated!=(self.values(),self.font_stamp()):raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            values=self.values();self.invalidate();self.result_object=backend.create(self.doc,*values)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

    def done(self,result):
        self.timer.stop();self.invalidate();super().done(result)


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():
        raise ValueError(tr('文書を開き、現在の編集を終了してください。','Open a document and finish the current edit.'))
    return TextSketchDialog(ws).exec_()
