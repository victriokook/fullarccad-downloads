"""Review and create a native local BOM snapshot without touching geometry."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from i18n import tr
import model_bom


class BomDialog(W.QDialog):
    def __init__(self,ws):
        doc=App.ActiveDocument;rows,stamp=model_bom.collect(doc)
        super().__init__(ws.main)
        self.setObjectName('FullArcBOMDialog');self.setWindowTitle(tr('部品表を作成','Create Bill of Materials'))
        self.doc=doc;self.ws=ws;self.stamp=stamp
        layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('全コンポーネント（非表示も含む）を元ボディごとに集計します。元ボディは数えません。\n作成時点のスナップショットです。自動更新・階層集計・クラウド管理はありません。',
                        'Groups all components, including hidden ones, by source body. Source bodies are not counted.\nCreates a snapshot; no automatic updates, hierarchy report or cloud management.'))
        note.setWordWrap(True);layout.addWidget(note)
        self.table=W.QTableWidget(len(rows),4);self.table.setObjectName('BOMPreview')
        self.table.setHorizontalHeaderLabels([tr('項目','Item'),tr('部品名','Part Name'),tr('元ボディID','Source Body ID'),tr('数量','Quantity')])
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        for row,(index,key,label,count) in enumerate(rows):
            for col,value in enumerate((index,label,key,count)):self.table.setItem(row,col,W.QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents();layout.addWidget(self.table)
        self.status=W.QLabel(tr('集計数量：','Total quantity: ')+str(sum(r[3] for r in rows)));layout.addWidget(self.status)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel)
        self.ok=buttons.button(W.QDialogButtonBox.Ok);self.ok.setText(tr('スプレッドシートを作成','Create Spreadsheet'))
        buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject));layout.addWidget(buttons)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.refresh_guard));self.timer.start()
        self.resize(740,390)

    def refresh_guard(self):
        try:
            if App.ActiveDocument is not self.doc or model_bom.collect(self.doc)[1]!=self.stamp:raise ValueError('stale')
        except Exception:
            self.ok.setEnabled(False);self.status.setText(tr('部品構成または文書が変わりました。閉じて開き直してください。','Components or document changed. Close and reopen.'))

    def accept(self):
        self.refresh_guard()
        if not self.ok.isEnabled():return
        try:self.result_sheet=model_bom.create(self.doc,self.stamp)
        except Exception as error:
            self.ok.setEnabled(False);self.status.setText(str(error));return
        super().accept()


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog():
        raise ValueError(tr('文書を開き、編集中のタスクを閉じてください。','Open a document and finish the current task.'))
    dialog=BomDialog(ws)
    try:
        if dialog.exec_()==W.QDialog.Accepted:
            dialog.result_sheet.ViewObject.showSheetMdi()
            ws.refresh()
            return dialog.result_sheet
    finally:dialog.timer.stop();dialog.deleteLater()
