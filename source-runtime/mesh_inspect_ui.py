import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_mesh_inspect as backend

class MeshInspectDialog(W.QDialog):
    def __init__(self,ws,source):
        super().__init__(ws.main);self.ws,self.source,self.doc=ws,source,source.Document;self.initial=backend.stamp(source);self.report=None
        self.setObjectName('FluxMeshInspect');self.setWindowTitle(tr('メッシュを検査','Inspect Mesh'));form=W.QFormLayout(self);form.addRow(tr('原本','Source'),W.QLabel(source.Label))
        note=W.QLabel(tr('読み取り専用の診断です。修復・形状変更・解析保存は行いません。nativeの閉鎖性、法線整合、非多様体辺、自己交差と、退化面数・面積を表示します。符号付き体積は閉鎖・整合し、検出された欠陥がない場合のみ表示します。複数成分の体積は合計です。全欠陥の検出や製造適性を保証しません。面グループ、重複面／頂点、非多様体頂点、折れ、誤差許容設定、箇所の強調表示は対象外です。',
            'Read-only diagnostics; no repair, geometry changes or saved analysis. Shows native closure, orientation consistency, nonmanifold edges and self-intersections, plus degenerate-facet count and area. Signed volume is shown only for closed, consistent meshes without detected defects; multiple components are summed. This is not a complete defect or manufacturing certificate. No face groups, duplicate face/point checks, nonmanifold-point checks, folds, tolerance controls or location highlighting.'));note.setWordWrap(True);form.addRow(note)
        self.result_text=W.QPlainTextEdit();self.result_text.setReadOnly(True);self.result_text.setMinimumSize(430,280);form.addRow(self.result_text);self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.analyze_button=W.QPushButton(tr('検査','Analyze'));form.addRow(self.analyze_button);self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Close);form.addRow(self.buttons);self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));self.analyze_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.analyze))
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()

    def guard(self):
        if App.ActiveDocument is not self.doc or self.doc.getObject(self.source.Name) is not self.source or self.ws.current_sketch() or backend.stamp(self.source)!=self.initial:raise ValueError(tr('原本または文書が変わりました。開き直してください。','The source or document changed. Reopen this dialog.'))

    def invalidate(self):self.report=None;self.result_text.clear()

    def refresh_guard(self):
        try:self.guard()
        except Exception as error:self.invalidate();self.analyze_button.setEnabled(False);self.status.setText(str(error))

    def analyze(self):
        self.invalidate()
        try:
            self.guard();r=backend.inspect(self.doc,self.source);yes=tr('はい','Yes');no=tr('いいえ','No');na=tr('対象外','Not applicable')
            rows=[(tr('三角形数','Triangles'),r['facets']),(tr('頂点数','Vertices'),r['vertices']),(tr('連結成分数','Connected components'),r['components']),
                (tr('閉じている','Closed'),yes if r['closed'] else no),(tr('法線整合','Consistent orientation'),yes if r['consistent'] else no),
                (tr('非多様体辺あり','Nonmanifold edges detected'),yes if r['nonmanifold'] else no),(tr('自己交差あり','Self-intersections detected'),yes if r['self_intersection'] else no),
                (tr('退化三角形数','Degenerate triangles'),r['degenerate_count']),(tr('面積','Area'),format(r['area'],'.12g')+' mm²'),
                (tr('符号付き体積（合計）','Signed volume (total)'),na if r['signed_volume'] is None else format(r['signed_volume'],'.12g')+' mm³')]
            self.result_text.setPlainText('\n'.join(str(k)+': '+str(v) for k,v in rows));self.report=r;self.status.setText(tr('検査結果（読み取り専用）','Inspection results (read-only)'))
        except Exception as error:self.status.setText(str(error))

    def done(self,result):self.timer.stop();self.invalidate();super().done(result)

def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx()
    if len(selected)!=1 or selected[0].SubElementNames:raise ValueError(tr('メッシュ全体を1つ選択してください。','Select one whole mesh.'))
    source=selected[0].Object;backend.validate(App.ActiveDocument,source);return MeshInspectDialog(ws,source).exec_()
