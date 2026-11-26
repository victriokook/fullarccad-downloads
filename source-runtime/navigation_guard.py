"""Keep native framing consistent and avoid unintended blank documents."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from i18n import tr


class NativeFitGuard(QtCore.QObject):
    def __init__(self, ws):
        super().__init__(ws.main)
        self.ws = ws
        self.actions = []
        self.busy = False
        for action in ws.main.findChildren(QtGui.QAction):
            if action.objectName() == 'Std_ViewFitAll':
                self.actions.append(action)
                action.installEventFilter(self)
                action.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(self.refit))

    def eventFilter(self, obj, event):
        doc = Gui.activeDocument()
        if (event.type() == QtCore.QEvent.Shortcut and obj in self.actions
                and doc and hasattr(doc.activeView(), 'getCameraOrientation')):
            self.refit()
            event.accept()
            return True
        return False

    def refit(self, *args):
        if self.busy:
            return
        doc = Gui.activeDocument()
        if not doc or not hasattr(doc.activeView(), 'getCameraOrientation'):
            return
        self.busy = True
        try:
            self.ws.fit()
        finally:
            self.busy = False

    def close(self):
        for action in self.actions:
            try:
                action.triggered.disconnect(__import__('builtins')._fullarc_qt_slot(self.refit))
                action.removeEventFilter(self)
            except (RuntimeError, TypeError):
                pass
        self.actions.clear()


def document_for_creation(app=App):
    doc = app.ActiveDocument
    if doc is not None:
        return doc
    if app.listDocuments():
        raise ValueError(tr('既存の文書をアクティブにしてから作成してください。',
                            'Activate an existing document before creating geometry.'))
    return app.newDocument('Untitled')
