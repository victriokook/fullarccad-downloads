import FreeCAD as App,FreeCADGui as Gui
from PySide import QtCore,QtWidgets as W
from pivy import coin
from i18n import tr
import model_cam_sim as m

def mesh_node(points,faces,color):
    node=coin.SoSeparator();mat=coin.SoMaterial();mat.diffuseColor=color;node.addChild(mat);coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),[tuple(p) for p in points]);node.addChild(coords);fs=coin.SoIndexedFaceSet();indices=[v for face in faces for v in (*face,-1)];fs.coordIndex.setValues(0,len(indices),indices);node.addChild(fs);return node

class SimulationDialog(W.QDialog):
    def __init__(self,ws,ops):
        super().__init__(ws.main);self.setWindowTitle(tr('加工シミュレーション','Machining Simulation'));self.resize(850,650);self.ops=ops;self.engine=None;layout=W.QVBoxLayout(self);self.combo=W.QComboBox()
        for op in ops:self.combo.addItem(op.Label,op.Name)
        layout.addWidget(self.combo);self.resolution=W.QDoubleSpinBox();self.resolution.setRange(.1,5);self.resolution.setDecimals(2);self.resolution.setValue(.5);self.resolution.setSuffix(' mm');layout.addWidget(self.resolution)
        hint=W.QLabel(tr('単一操作の直線エンドミル経路と素材除去の近似表示。格子幅mmで精度を指定します。\n円弧・穴あけサイクル・複数操作連結は対象外。衝突判定・寸法保証・機械通信なし。','Approximate stock removal for one linear endmill operation;grid spacing in mm.\nNo arcs,drilling cycles or multi-operation sequence. No collision detection,dimensional guarantee or machine connection.'));hint.setWordWrap(True);layout.addWidget(hint)
        previous=set(ws.main.findChildren(W.QMdiSubWindow));self.native_view=Gui.createViewer();self.native_view.setAnimationEnabled(False)
        created=set(ws.main.findChildren(W.QMdiSubWindow))-previous
        if len(created)!=1:raise ValueError('Could not identify dedicated preview')
        self.view=created.pop();self.view.setParent(self);layout.addWidget(self.view,1);self.scene=coin.SoSeparator();self.content=coin.SoSeparator();self.scene.addChild(self.content);self.root=self.native_view.getSceneGraph();self.root.addChild(self.scene);self.native_view.viewIsometric()
        row=W.QHBoxLayout();layout.addLayout(row)
        for attr,ja,en,fn in [('reset','初期化','Reset',self.reset_sim),('play','再生','Play',self.play_sim),('pause','一時停止','Pause',self.pause_sim),('step_button','1命令進む','Step',self.advance)]:
            btn=W.QPushButton(tr(ja,en));setattr(self,attr,btn);btn.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(fn));row.addWidget(btn)
        self.status=W.QLabel();layout.addWidget(self.status);close=W.QPushButton(tr('閉じる','Close'));close.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.reject));layout.addWidget(close);self.timer=QtCore.QTimer(self);self.timer.setInterval(80);self.timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.advance));self.guard_timer=QtCore.QTimer(self);self.guard_timer.setInterval(400);self.guard_timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(self.guard));self.guard_timer.start();self.combo.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.resolution.valueChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
    def invalidate(self,*args):
        self.timer.stop();self.engine=None;self.content.removeAllChildren();self.status.setText(tr('初期化してください。','Press Reset.'))
    def reset_sim(self):
        self.invalidate()
        try:self.engine=m.Simulation(self.ops[self.combo.currentIndex()],self.resolution.value());self.render();self.native_view.fitAll()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def render(self):
        self.content.removeAllChildren()
        for mesh,color in zip(self.engine.meshes(),((.65,.65,.72),(.95,.7,.25))):
            pts,faces=mesh.Topology;self.content.addChild(mesh_node(pts,faces,color))
        points,faces=self.engine.tool.tessellate(.1);tool=coin.SoSeparator();move=coin.SoTranslation();move.translation=tuple(self.engine.position.Base);tool.addChild(move);tool.addChild(mesh_node(points,faces,(.2,.6,.9)));self.content.addChild(tool);self.status.setText(str(self.engine.index)+' / '+str(len(self.engine.commands)));self.native_view.redraw()
    def advance(self):
        if self.engine is None:return
        try:
            if not self.engine.step():self.timer.stop()
            self.render()
        except Exception as error:self.invalidate();self.status.setText(str(error))
    def play_sim(self):
        if self.engine is not None:self.timer.start()
    def pause_sim(self):self.timer.stop()
    def guard(self):
        if self.engine is None:return
        try:self.engine.valid()
        except Exception:self.invalidate();self.status.setText(tr('入力が変わりました。初期化してください。','Inputs changed. Reset required.'))
    def cleanup(self):self.timer.stop();self.guard_timer.stop();self.engine=None;self.content.removeAllChildren();self.root.removeChild(self.scene);self.view.close()

def show(ws):
    ops=[o for o in App.ActiveDocument.Objects if any(getattr(o,n,False) for n in ('FullArcCAMPocket','FullArcCAMFacing'))] if App.ActiveDocument else []
    if not ops:raise ValueError(tr('先に対応するエンドミル加工を作成してください。','Create a supported endmill operation first.'))
    dialog=SimulationDialog(ws,ops)
    try:dialog.exec_()
    finally:dialog.cleanup();dialog.deleteLater()
