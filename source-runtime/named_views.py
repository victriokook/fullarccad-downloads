"""Document-local native camera bookmarks; model objects are untouched."""
import json,math,struct
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from pivy import coin
from i18n import tr
from named_view_name import validate_name,renamed_entries

KEY='FluxCAD.NamedViews.v1'
FIELDS=('position','orientation','nearDistance','farDistance','focalDistance','aspectRatio','viewportMapping','extent','type')


def validate_camera(data):
    if type(data) is not dict or set(data)!=set(FIELDS) or data['type'] not in ('Orthographic','Perspective'):
        raise ValueError('Invalid saved camera format')
    def number(value):
        try:
            if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>3e38:raise ValueError('Invalid camera number')
            native=struct.unpack('f',struct.pack('f',value))[0]
            if value!=0 and native==0:raise ValueError('Camera number underflow')
            return native
        except OverflowError as error:raise ValueError('Camera number overflow') from error
    for key,length in (('position',3),('orientation',4)):
        if type(data[key]) not in (list,tuple) or len(data[key])!=length:raise ValueError('Invalid camera vector')
        for value in data[key]:number(value)
    if abs(math.hypot(*data['orientation'])-1)>1e-6:raise ValueError('Invalid camera rotation')
    for key in ('nearDistance','farDistance','focalDistance','aspectRatio','extent'):number(data[key])
    if not number(data['nearDistance'])<number(data['farDistance']) or min(data['focalDistance'],data['aspectRatio'],data['extent'])<=0:raise ValueError('Invalid camera extents')
    if data['type']=='Perspective' and data['nearDistance']<=0:raise ValueError('Perspective near distance must be positive')
    if data['type']=='Perspective' and data['extent']>=math.pi:raise ValueError('Invalid perspective angle')
    if type(data['viewportMapping']) is not int or not 0<=data['viewportMapping']<=4:raise ValueError('Invalid viewport mapping')
    return data


def current_view(doc):
    if doc is None or App.ActiveDocument is not doc or App.getDocument(doc.Name) is not doc:
        raise ValueError(tr('元の文書を開いてください。','Return to the original document.'))
    gui=Gui.activeDocument();view=gui.activeView() if gui else None
    if view is None or not hasattr(view,'getCameraNode'):raise ValueError(tr('3Dビューを開いてください。','Open a3D view.'))
    return view


def capture(doc):
    view=current_view(doc);camera=view.getCameraNode();kind=view.getCameraType()
    return validate_camera(dict(type=kind,position=list(camera.position.getValue().getValue()),orientation=list(camera.orientation.getValue().getValue()),nearDistance=camera.nearDistance.getValue(),farDistance=camera.farDistance.getValue(),focalDistance=camera.focalDistance.getValue(),aspectRatio=camera.aspectRatio.getValue(),viewportMapping=camera.viewportMapping.getValue(),extent=(camera.height if kind=='Orthographic' else camera.heightAngle).getValue()))


def entries(doc):
    current_view(doc);raw=doc.Meta.get(KEY,'{}')
    if type(raw) is not str or len(raw)>200000:raise ValueError('Invalid named-view data')
    try:data=json.loads(raw)
    except (ValueError,TypeError) as error:raise ValueError('Invalid named-view data') from error
    if type(data) is not dict or len(data)>50:raise ValueError('Use at most50 named views')
    for name,camera in data.items():validate_name(name);validate_camera(camera)
    return data


def write(doc,data):
    current_view(doc);meta=dict(doc.Meta);meta[KEY]=json.dumps(data,ensure_ascii=False,separators=(',',':'));doc.Meta=meta
    if entries(doc)!=data:raise ValueError('Named-view storage failed')


def save(doc,name,replace=False):
    name=validate_name(name);data=entries(doc)
    if type(replace) is not bool:raise ValueError('Invalid replace setting')
    if replace and name not in data:raise ValueError('Select a saved view to update')
    if not replace and name in data:raise ValueError(tr('同じ名前が既にあります。','That name already exists.'))
    if not replace and len(data)>=50:raise ValueError('Use at most50 named views')
    data[name]=capture(doc);write(doc,data)


def rename(doc,old_name,new_name):
    data=entries(doc);changed=renamed_entries(data,old_name,new_name)
    if old_name!=new_name:write(doc,changed)


def remove(doc,name):
    data=entries(doc)
    if name not in data:raise ValueError('Select a saved view')
    del data[name];write(doc,data)


def restore(doc,name):
    data=entries(doc)
    if name not in data:raise ValueError('Select a saved view')
    data=validate_camera(data[name]);view=current_view(doc);old=view.getCamera();animation=view.isAnimationEnabled()
    try:
        view.setAnimationEnabled(False);view.setCameraType(data['type']);camera=view.getCameraNode()
        camera.position.setValue(*data['position']);camera.orientation.setValue(coin.SbRotation(*data['orientation']))
        for key in ('nearDistance','farDistance','focalDistance','aspectRatio','viewportMapping'):getattr(camera,key).setValue(data[key])
        (camera.height if data['type']=='Orthographic' else camera.heightAngle).setValue(data['extent']);view.redraw()
    except Exception:
        view.setCamera(old);raise
    finally:view.setAnimationEnabled(animation)


class NamedViewsDialog(W.QDialog):
    def __init__(self,ws):
        super().__init__(ws.main);self.doc=App.ActiveDocument;self.ws=ws;self.setObjectName('FluxNamedViews');self.setWindowTitle(tr('名前付きビュー','Named Views'));self.resize(430,400)
        layout=W.QVBoxLayout(self);note=W.QLabel(tr('位置・向き・ズーム・投影方式を最大50件保存します。文書を保存すると再読込できます。追加・名前変更・更新・削除は即時反映し、Undoには対応しません。','Save up to50 camera positions, orientations, zoom levels and projection types. Save the document to retain them after reopening. Add/rename/update/delete apply immediately and do not support Undo.'));note.setWordWrap(True);layout.addWidget(note)
        self.list=W.QListWidget();layout.addWidget(self.list);self.name=W.QLineEdit();self.name.setMaxLength(64);self.name.setPlaceholderText(tr('新規・変更するビュー名','New or replacement view name'));name_row=W.QHBoxLayout();name_row.addWidget(self.name);self.rename_button=W.QPushButton(tr('名前変更','Rename'));name_row.addWidget(self.rename_button);self.rename_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.rename));layout.addLayout(name_row)
        row=W.QHBoxLayout();layout.addLayout(row)
        for key,ja,en,fn in [('add','現在の視点を追加','Add Current',self.add),('restore','復元','Restore',self.restore),('update','現在の視点で更新','Update Current',self.update),('delete','削除','Delete',self.delete)]:
            button=W.QPushButton(tr(ja,en));setattr(self,key+'_button',button);row.addWidget(button);button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(fn))
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);close=W.QPushButton(tr('閉じる','Close'));close.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.accept));layout.addWidget(close);self.reload()
    def reload(self):
        self.list.clear();self.list.addItems(list(entries(self.doc)));self.stamp=self.doc.Meta.get(KEY,'{}')
    def selected(self):
        item=self.list.currentItem()
        if item is None:raise ValueError(tr('保存済みビューを選択してください。','Select a saved view.'))
        return item.text()
    def perform(self,fn):
        try:
            current_view(self.doc)
            if self.doc.Meta.get(KEY,'{}')!=self.stamp:raise ValueError(tr('一覧が変わりました。開き直してください。','The saved list changed. Reopen this dialog.'))
            fn();self.reload();self.status.setText(tr('完了','Done'))
        except Exception as error:self.status.setText(str(error))
    def add(self):self.perform(__import__('builtins')._fullarc_qt_slot(lambda:save(self.doc,self.name.text()),(0, 0, False, False)))
    def rename(self):self.perform(__import__('builtins')._fullarc_qt_slot(lambda:rename(self.doc,self.selected(),self.name.text()),(0, 0, False, False)))
    def restore(self):self.perform(__import__('builtins')._fullarc_qt_slot(lambda:restore(self.doc,self.selected()),(0, 0, False, False)))
    def update(self):self.perform(__import__('builtins')._fullarc_qt_slot(lambda:save(self.doc,self.selected(),True),(0, 0, False, False)))
    def delete(self):self.perform(__import__('builtins')._fullarc_qt_slot(lambda:remove(self.doc,self.selected()),(0, 0, False, False)))


def show(ws):
    if ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget() or any(getattr(value,'active',False) is True for value in vars(ws).values()):raise ValueError(tr('編集中の操作を終了してください。','Finish the active edit first.'))
    current_view(App.ActiveDocument)
    return NamedViewsDialog(ws).exec_()
