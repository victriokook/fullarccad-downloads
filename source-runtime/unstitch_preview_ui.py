"""Candidate preview only. Commit intentionally absent until history passes."""
from types import SimpleNamespace
import FreeCAD as App
import Part
from PySide import QtCore,QtWidgets as W
from extrude_panel import ExtrudePanel
from i18n import tr
from model_defeature import fingerprint,containers
import model_unstitch as backend

class PreviewDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.source=source;self.doc=source.Document
        self.setObjectName('FluxUnstitchPreview');self.setWindowTitle(tr('面を分離 — プレビュー候補','Unstitch — Preview Candidate'))
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.parts=[];self.loaded=None
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('全ての面を個別に確認します。履歴の問題を検証中のため、この候補からは確定できません。','Inspect every individual face. Commit is unavailable while linked-history validation is pending.'));self.note=note;note.setWordWrap(True);layout.addWidget(note)
        self.list=W.QListWidget();layout.addWidget(self.list);self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview_button=W.QPushButton(tr('面を取得','Load Faces'));layout.addWidget(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Close);layout.addWidget(self.buttons)
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.compute));self.list.currentRowChanged.connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh));self.timer.start()
    def stamp(self):
        backend.checked(self.doc,self.source)
        return fingerprint(self.source),tuple(self.source.getGlobalPlacement().toMatrix().A),tuple(p.Name for p in containers(self.source))
    def clear(self):
        ExtrudePanel.clear_preview(self.host);self.loaded=None;self.parts=[];self.list.clear()
    def compute(self):
        self.clear()
        try:
            if App.ActiveDocument!=self.doc:raise ValueError(tr('元の文書に戻ってください。','Return to the original document.'))
            self.parts=backend.faces(self.doc,self.source);self.loaded=self.stamp()
            for i,face in enumerate(self.parts):self.list.addItem(tr('面 %d — 面積 %.6g mm²','Face %d — Area %.6g mm²')%(i+1,face.Area))
            self.status.setText(tr('全%d面。原本を保持します。','All %d faces. Source is retained.')%len(self.parts));self.list.setCurrentRow(0)
        except Exception as error:self.clear();self.status.setText(str(error))
    def preview(self,index):
        ExtrudePanel.clear_preview(self.host)
        if not 0<=index<len(self.parts):return
        try:
            if App.ActiveDocument!=self.doc or self.stamp()!=self.loaded:raise ValueError(tr('対象が変わりました。面を取得し直してください。','Input changed. Load faces again.'))
            ExtrudePanel.show_shape(self.host,self.parts[index],'new')
            self.host.hidden.append((self.source,bool(self.source.Visibility)));self.source.Visibility=False
        except Exception as error:self.clear();self.status.setText(str(error))
    def refresh(self):
        if self.loaded is None:return
        try:
            if App.ActiveDocument!=self.doc or self.stamp()!=self.loaded:raise ValueError(tr('対象が変わりました。面を取得し直してください。','Input changed. Load faces again.'))
        except Exception as error:self.clear();self.status.setText(str(error))
    def done(self,result):self.timer.stop();self.clear();super().done(result)
