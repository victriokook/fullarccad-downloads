"""Restore document save metadata when a write fails; keep native errors visible."""
from pathlib import Path
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtGui,QtWidgets as W
from i18n import tr

def _modified(doc):
    gd=Gui.getDocument(doc.Name)
    return bool(gd.Modified)

def _restore(doc,filename,label,modified):
    doc.FileName=filename
    if doc.Label!=label:doc.Label=label
    Gui.getDocument(doc.Name).Modified=modified

def write(doc,filename=None):
    """Save synchronously; failure must not change FileName, label or dirty flag."""
    previous=(doc.FileName,doc.Label,_modified(doc))
    try:
        result=doc.saveAs(str(filename)) if filename is not None else doc.save()
        if result is False:raise OSError(tr('保存できませんでした。','The document could not be saved.'))
    except Exception:
        _restore(doc,*previous)
        raise
    # App.Document.save[As]() does not clear Gui.Document.Modified itself.
    # Native GUI commands normally do this after a successful return.
    Gui.getDocument(doc.Name).Modified=False
    return True

def save(ws,save_as=False):
    doc=App.ActiveDocument
    if doc is None:raise ValueError(tr('保存する文書を開いてください。','Open a document to save.'))
    name=doc.Name;filename=None
    if save_as or not doc.FileName:
        filename,_=W.QFileDialog.getSaveFileName(ws.main,tr('名前を付けて保存','Save As'),doc.FileName or doc.Label+'.FCStd','FreeCAD (*.FCStd)')
        if not filename:return False
        if not filename.lower().endswith('.fcstd'):
            filename+='.FCStd'
            if Path(filename).exists():
                answer=W.QMessageBox.question(ws.main,tr('上書き確認','Confirm Overwrite'),tr('既存のファイルを上書きしますか？','Overwrite the existing file?'),W.QMessageBox.Yes|W.QMessageBox.No,W.QMessageBox.No)
                if answer!=W.QMessageBox.Yes:return False
        if App.ActiveDocument is not doc or App.getDocument(name) is not doc:
            raise ValueError(tr('文書が変更されたため保存を中止しました。','The active document changed; saving was cancelled.'))
    write(doc,filename)
    try:
        import recent_files
        recent_files.remember(doc.FileName)
    except Exception as error:App.Console.PrintWarning('FullArcCAD recent files: '+str(error)+'\n')
    ws.main.statusBar().showMessage(tr('保存しました：','Saved: ')+doc.FileName,6000)
    return True

class SaveGuard(QtCore.QObject):
    """Guard Ctrl+S and repair failed native-menu/close Save As operations.

    Native successful saves advance the known destination via the observer.
    An unchanged destination or a cancelled dialog requires no action. The
    fallback repairs a changed destination only after a native command returns;
    it never changes filenames on a timer or on ordinary document edits.
    """
    NATIVE_SAVE=('Std_Save','Std_SaveAs')
    NATIVE_REPAIR=NATIVE_SAVE+('Std_SaveAll','Std_Close','Std_CloseAll','Std_Quit')
    def __init__(self,ws):
        super().__init__(ws.main);self.ws=ws;self.paths={};self.actions=[];self.closed=False
        for doc in App.listDocuments().values():self.record(doc)
        App.addDocumentObserver(self)
        for action in ws.main.findChildren(QtGui.QAction):
            if action.objectName() in self.NATIVE_REPAIR:
                self.actions.append(action);action.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(self.native_finished))
                if action.objectName() in self.NATIVE_SAVE:action.installEventFilter(self)
    def record(self,doc):self.paths[doc.Name]=(doc,doc.FileName)
    def slotCreatedDocument(self,doc):self.record(doc)
    def slotFinishRestoreDocument(self,doc,*args):self.record(doc)
    def slotFinishSaveDocument(self,doc,*args):self.record(doc)
    def slotDeletedDocument(self,doc):self.paths.pop(doc.Name,None)
    def eventFilter(self,obj,event):
        if event.type()==QtCore.QEvent.Shortcut and obj.objectName() in self.NATIVE_SAVE:
            self.ws.safe(__import__('builtins')._fullarc_qt_slot(lambda:save(self.ws,obj.objectName()=='Std_SaveAs'),(0, 0, False, False)))
            event.accept();return True
        return False
    def native_finished(self,*args):
        sender=self.sender()
        all_docs=sender is not None and sender.objectName() in ('Std_SaveAll','Std_CloseAll','Std_Quit')
        for name,(doc,previous) in list(self.paths.items()):
            try:
                if App.getDocument(name) is not doc:continue
                if not all_docs and App.ActiveDocument is not doc:continue
                if doc.FileName!=previous:
                    doc.FileName=previous
                    # A failed native write must remain visibly unsaved.
                    Gui.getDocument(name).Modified=True
                    App.Console.PrintWarning(tr('保存に失敗したため、元の保存先を復元しました。\n','Saving failed; the previous destination was restored.\n'))
            except (RuntimeError,ReferenceError):self.paths.pop(name,None)
    def close(self):
        if self.closed:return
        self.closed=True;App.removeDocumentObserver(self)
        for action in self.actions:
            try:action.triggered.disconnect(__import__('builtins')._fullarc_qt_slot(self.native_finished));action.removeEventFilter(self)
            except (RuntimeError,TypeError):pass
        self.actions.clear();self.paths.clear()
