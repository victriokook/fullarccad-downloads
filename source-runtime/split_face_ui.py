import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from types import SimpleNamespace
from extrude_panel import ExtrudePanel
from i18n import tr
import model_split_face as backend


def stamp(obj):
    return (obj.Shape.hashCode(),tuple(obj.getGlobalPlacement().toMatrix().A),
            tuple(o.Name for o in backend.parents([obj])))


class SplitFaceDialog(W.QDialog):
    def __init__(self,ws,source,face,tool,existing=None):
        super().__init__(ws.main)
        self.ws,self.source,self.doc,self.existing=ws,source,source.Document,existing
        self.host=SimpleNamespace(overlay=None,hidden=[],preview_shape=None);self.validated=None
        self.setObjectName('FluxSplitFace');self.setWindowTitle(tr('面を分割','Split Face'));self.setMinimumWidth(450)
        form=W.QFormLayout(self)
        self.face=W.QComboBox()
        for i,f in enumerate(source.Shape.Faces):self.face.addItem('Face'+str(i+1),'Face'+str(i+1))
        self.face.setCurrentIndex(self.face.findData(face));form.addRow(tr('対象面','Target face'),self.face)
        self.tool=W.QComboBox();self.inputs={source.Name:(source,stamp(source))}
        for obj in self.doc.Objects:
            if obj!=source and obj!=existing and not getattr(obj,'FluxCADInternal',False) and hasattr(obj,'Shape') and not obj.Shape.Faces and obj.Shape.Edges:
                self.tool.addItem(obj.Label+' ['+obj.Name+']',obj.Name);self.inputs[obj.Name]=(obj,stamp(obj))
        self.tool.setCurrentIndex(self.tool.findData(tool.Name));form.addRow(tr('面上の工具','On-face tool'),self.tool)
        note=W.QLabel(tr('平面・円柱面と、その面上に全体が載る1本の辺またはワイヤ。全領域を残し、体積を保って面だけを分割します。自動投影・延長はありません。元のボディは保持されます。',
                             'Select a planar/cylindrical face and one edge or wire entirely on it. Retains every region and the solid volume. No automatic projection or extension. The source body is retained.'))
        note.setWordWrap(True);form.addRow(note)
        self.status=W.QLabel();self.status.setWordWrap(True);form.addRow(self.status)
        self.preview_button=W.QPushButton(tr('プレビュー','Preview'));form.addRow(self.preview_button)
        self.buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);form.addRow(self.buttons);self.ok=self.buttons.button(W.QDialogButtonBox.Ok);self.ok.setEnabled(False)
        self.face.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate));self.tool.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(self.invalidate))
        self.preview_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.preview));self.buttons.accepted.connect(__import__('builtins')._fullarc_qt_slot(self.accept));self.buttons.rejected.connect(__import__('builtins')._fullarc_qt_slot(self.reject))
        self.existing_stamp=stamp(existing) if existing else None

    def selected_tool(self):return self.doc.getObject(self.tool.currentData() or '')
    def values(self):return self.face.currentData(),self.tool.currentData()
    def guard(self):
        if App.ActiveDocument is not self.doc or self.ws.current_sketch():raise ValueError('The active document or edit changed')
        for obj in (self.source,self.selected_tool()):
            if not obj or obj.Name not in self.inputs or self.doc.getObject(obj.Name) is not obj or stamp(obj)!=self.inputs[obj.Name][1]:
                raise ValueError(tr('参照が変わりました。画面を開き直してください。','An input changed. Reopen the dialog.'))
        if self.existing and (self.doc.getObject(self.existing.Name) is not self.existing or stamp(self.existing)!=self.existing_stamp):
            raise ValueError('The result changed. Reopen the dialog')

    def invalidate(self,*_):
        ExtrudePanel.clear_preview(self.host);self.validated=None;self.ok.setEnabled(False)
    def preview(self):
        self.invalidate()
        try:
            self.guard();shape=backend.preview(self.doc,self.source,self.face.currentData(),self.selected_tool(),self.existing)
            ExtrudePanel.show_shape(self.host,shape,'new');target=self.existing or self.source
            self.host.hidden.append((target,bool(target.Visibility)));target.Visibility=False
            self.validated=self.values();self.ok.setEnabled(True)
            self.status.setText(tr('面数: %d → %d / ソリッド数: 1','Faces: %d → %d / Solids: 1')%(len(self.source.Shape.Faces),len(shape.Faces)))
        except Exception as error:self.status.setText(str(error))
    def accept(self):
        try:
            self.guard()
            if self.validated!=self.values():raise ValueError(tr('先にプレビューしてください。','Preview first.'))
            self.invalidate();self.result_object=backend.apply(self.doc,self.source,self.face.currentData(),self.selected_tool(),self.existing)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(self.result_object);self.ws.refresh()
        except Exception as error:self.status.setText(str(error));return
        super().accept()
    def done(self,result):self.invalidate();super().done(result)


def show(ws):
    if not App.ActiveDocument or ws.current_sketch() or Gui.Control.activeDialog() or W.QApplication.activeModalWidget():
        raise ValueError(tr('現在の編集を終了してください。','Finish the current edit.'))
    selected=Gui.Selection.getSelectionEx();existing=None
    if len(selected)==1 and getattr(selected[0].Object,'FluxSplitFace',False) and not selected[0].SubElementNames:
        existing=selected[0].Object;source,tool,face=existing.Source,existing.Tool,existing.FaceName
    elif len(selected)==2:
        faces=[s for s in selected if len(s.SubElementNames)==1 and s.SubElementNames[0].startswith('Face')]
        tools=[s for s in selected if not s.SubElementNames]
        if len(faces)!=1 or len(tools)!=1:raise ValueError('Select one body FaceN and one whole tool')
        source,tool,face=faces[0].Object,tools[0].Object,faces[0].SubElementNames[0]
    else:raise ValueError(tr('ボディの面1つと工具全体を選択してください。','Select one body face and one whole tool.'))
    backend.checked(App.ActiveDocument,source,tool,existing)
    return SplitFaceDialog(ws,source,face,tool,existing).exec_()
