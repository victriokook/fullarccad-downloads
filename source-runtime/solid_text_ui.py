from types import SimpleNamespace
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets as W
from i18n import tr
from extrude_panel import ExtrudePanel
import model_solid_text as backend


class TextDialog(W.QDialog):
    def __init__(self, ws, existing=None):
        super().__init__(ws.main)
        self.ws, self.existing, self.doc = ws, existing, App.ActiveDocument
        self.initial_stamp = backend.stamp(existing)
        self.host = SimpleNamespace(overlay=None, hidden=[], preview_shape=None)
        self.validated = None
        self.setObjectName('FluxSolidText')
        self.setWindowTitle(tr('文字ソリッド', 'Solid Text'))
        self.setMinimumWidth(470)
        form = W.QFormLayout(self)
        self.text = W.QLineEdit(existing.Base.String if existing else 'FluxCAD')
        self.text.setMaxLength(100)
        from pathlib import Path
        default_font='C:/Windows/Fonts/meiryo.ttc'
        if not Path(default_font).is_file():default_font='C:/Windows/Fonts/arial.ttf'
        self.font = W.QLineEdit(existing.Base.FontFile if existing else default_font)
        row = W.QWidget();layout = W.QHBoxLayout(row);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.font);browse = W.QPushButton(tr('参照…', 'Browse…'));layout.addWidget(browse)
        form.addRow(tr('文字', 'Text'), self.text);form.addRow(tr('フォントファイル', 'Font file'), row)
        self.size, self.tracking, self.depth = (W.QDoubleSpinBox() for _ in range(3))
        self.original_numbers=[]
        self.display_numbers=[]
        for field, low, high, value, label in (
                (self.size,.1,1000,existing.Base.Size.Value if existing else 10,tr('文字高さ', 'Text height')),
                (self.tracking,-1000,1000,existing.Base.Tracking.Value if existing else 0,tr('字間の追加距離', 'Additional tracking')),
                (self.depth,.001,1000,existing.Dir.Length if existing else 2,tr('厚さ', 'Thickness'))):
            field.setRange(low,high);field.setDecimals(8);field.setSuffix(' mm');field.setValue(value);form.addRow(label,field)
            self.original_numbers.append(value);self.display_numbers.append(field.value())
        self.alignment=W.QComboBox();self.reference=W.QComboBox()
        for vertical,ja_v in [('Top','上'),('Middle','中央'),('Bottom','下')]:
            for horizontal,ja_h in [('Left','左'),('Center','中央'),('Right','右')]:
                key=vertical+'-'+horizontal;self.alignment.addItem(tr(ja_v+'・'+ja_h,key),key)
        self.alignment.setCurrentIndex(self.alignment.findData(str(existing.Base.Justification) if existing else 'Bottom-Left'))
        self.reference.addItem(tr('大文字高さ','Cap Height'),'Cap Height');self.reference.addItem(tr('実際の字形範囲','Shape Height'),'Shape Height')
        self.reference.setCurrentIndex(self.reference.findData(str(existing.Base.JustificationReference) if existing else 'Cap Height'))
        form.addRow(tr('原点に対する文字揃え','Alignment at origin'),self.alignment);form.addRow(tr('縦方向の基準','Vertical reference'),self.reference)
        self.alignment.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.reference.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        note=W.QLabel(tr('日本語・英数記号1～100文字（1行）。対応字形を含むTTF/OTF/TTCを指定してください。初期位置はXY平面です。文字輪郭と標準押し出しを作成します。原点に対して文字を揃えます。複数文字は複数ソリッドになります。元のフォントファイルが必要です。',
                             'Use 1–100 Japanese/ASCII characters on one line, with a TTF/OTF/TTC containing the required glyphs. Starts on the XY plane. Creates text outlines and a native extrusion; alignment uses the text origin; separate letters form separate solids. The original font file is required.'))
        note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー', 'Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons)
        self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        for field in (self.size,self.tracking,self.depth):field.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.text.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.font.textChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        def choose():
            filename,_=W.QFileDialog.getOpenFileName(self,tr('フォントを選択', 'Choose Font'),self.font.text(),'Fonts (*.ttf *.otf *.ttc)')
            if filename:self.font.setText(filename)
        browse.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(choose));self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview))
        self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))

    def values(self):
        numbers=[original if field.value()==display else field.value()
                 for field,original,display in zip((self.size,self.tracking,self.depth),self.original_numbers,self.display_numbers)]
        return (self.text.text(),self.font.text(),*numbers,self.alignment.currentData(),self.reference.currentData())

    def guard(self):
        if (App.ActiveDocument is not self.doc or self.ws.current_sketch()
                or (self.existing is not None and
                    (self.doc.getObject(self.existing.Name) is not self.existing
                     or backend.stamp(self.existing)!=self.initial_stamp))):
            raise ValueError(tr('文書または対象が変わりました。画面を開き直してください。', 'The document or target changed. Reopen this dialog.'))

    def invalidate(self, *_):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)

    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.doc,*self.values()[:5],existing=self.existing,alignment=self.values()[5],reference=self.values()[6])
            ExtrudePanel.show_shape(self.host,shape,'new')
            if self.existing:
                self.host.hidden.append((self.existing,bool(self.existing.Visibility)));self.existing.Visibility=False
            self.validated=self.values();self.ok.setEnabled(True)
            self.status.setText(tr('ソリッド数: %d / 体積: %.6g mm³', 'Solids: %d / Volume: %.6g mm³')%(len(shape.Solids),shape.Volume))
        except Exception as error:self.status.setText(str(error))

    def accept(self):
        try:
            self.guard()
            if self.validated!=self.values():raise ValueError(tr('先にプレビューしてください。', 'Preview first.'))
            self.invalidate();self.result_object=backend.create(self.doc,*self.values()[:5],existing=self.existing,alignment=self.values()[5],reference=self.values()[6])
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()

    def done(self, result):
        self.invalidate();super().done(result)


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():
        raise ValueError(tr('文書を開き、現在の編集を終了してください。', 'Open a document and finish the current edit.'))
    selected=Gui.Selection.getSelection()
    existing=selected[0] if len(selected)==1 and backend.is_text(selected[0]) else None
    return TextDialog(ws,existing).exec_()
