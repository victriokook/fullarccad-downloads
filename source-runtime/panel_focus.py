"""Keep Qt focus in the current view when a main-window overlay closes."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets as W


def hide_modeling_panel(owner):
    panel = owner.panel
    try:
        focus = W.QApplication.focusWidget()
        if (panel.isVisible() and App.ActiveDocument == getattr(owner, 'doc', None)
                and focus is not None and (focus == panel or panel.isAncestorOf(focus))):
            document = Gui.activeDocument()
            view = document.activeView() if document else None
            if view is not None and hasattr(view, 'graphicsView'):
                view.graphicsView().viewport().setFocus(QtCore.Qt.OtherFocusReason)
    except (RuntimeError, ReferenceError):
        pass
    panel.hide()
