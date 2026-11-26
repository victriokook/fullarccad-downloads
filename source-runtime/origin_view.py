"""Origin-centred isometric camera action in the native NaviCube menu."""
import math
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtGui,QtWidgets as W
from i18n import tr
from pivy import coin

def available():
    gd=Gui.activeDocument()
    return bool(gd and gd.getInEdit() is None and hasattr(gd.activeView(),'getCameraNode'))

def go(ws):
    if not available():raise ValueError(tr('3Dビューを開き、編集中の操作を終了してください。','Open a 3D view and finish editing.'))
    view=Gui.activeDocument().activeView();node=view.getCameraNode();distance=float(node.focalDistance.getValue())
    if not math.isfinite(distance) or distance<=1e-9:raise ValueError('Invalid camera focal distance')
    # Camera +Z points towards the observer;X is along world(1,1,0).
    # This defines the standard isometric orientation without starting animation.
    rotation=App.Rotation(App.Vector(1,1,0),App.Vector(-1,1,2),App.Vector(1,-1,1),'ZXY')
    old=view.getCamera();animation=view.isAnimationEnabled()
    try:
        view.setAnimationEnabled(False)
        node.orientation.setValue(coin.SbRotation(*rotation.Q))
        node.focalDistance.setValue(distance)
        node.position.setValue(tuple(rotation.multVec(App.Vector(0,0,distance))))
        ws.grid.update()
    except Exception:view.setCamera(old);raise
    finally:view.setAnimationEnabled(animation)

class OriginMenu(QtCore.QObject):
    def __init__(self,ws):
        super().__init__(ws.main);self.ws=ws;self.actions=[];self.enabled=True
        W.QApplication.instance().installEventFilter(self)
        for menu in ws.main.findChildren(W.QMenu,'NaviCube_Menu'):self.install(menu)
    def install(self,menu):
        if not self.enabled:return
        action=next((a for a in menu.actions() if a.objectName()=='FullArcReturnToOrigin'),None)
        if action is None:
            action=QtGui.QAction(tr('原点に戻る','Return to Origin'),menu);action.setObjectName('FullArcReturnToOrigin')
            action.setToolTip(tr('原点を中央にして標準の斜め表示へ戻します。表示倍率は保持します。','Centre the world origin in the standard isometric view,keeping zoom.'))
            action.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False:self.ws.safe(__import__('builtins')._fullarc_qt_slot(lambda:go(self.ws),(0, 0, False, False))),(1, 0, False, False)))
            first=menu.actions()[0] if menu.actions() else None;menu.insertAction(first,action);self.actions.append(action)
        action.setEnabled(available())
    def eventFilter(self,obj,event):
        if self.enabled and event.type()==QtCore.QEvent.Show and isinstance(obj,W.QMenu) and obj.objectName()=='NaviCube_Menu':self.install(obj)
        return False
    def close(self):
        self.enabled=False;W.QApplication.instance().removeEventFilter(self)
        for action in self.actions:
            try:action.parent().removeAction(action);action.deleteLater()
            except RuntimeError:pass
        self.actions.clear()
