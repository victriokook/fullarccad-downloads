import primitive_precision
import coil_input_ui
"""Movable dimension/position editor for the four creation primitives."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from floating_panel import FloatingPanel
from i18n import tr
import model_primitives as primitives


class PrimitivePanel(FloatingPanel):
    layout_key='PrimitivePanel'
    preferred_height=650

    def __init__(self,ws):
        super().__init__(ws)
        policy=self.status.sizePolicy();policy.setHeightForWidth(True);self.status.setSizePolicy(policy)

    def build_fields(self,form):
        form.setRowWrapPolicy(W.QFormLayout.WrapLongRows)
        self.form=form;self.fields={};self.labels={}
        def field(key,label,widget):
            self.fields[key]=widget;self.labels[key]=W.QLabel(label)
            widget.setSizePolicy(W.QSizePolicy.Ignored,W.QSizePolicy.Fixed)
            form.addRow(self.labels[key],widget)
            return widget
        self.path=field('path',tr('経路','Path'),W.QComboBox())
        for key,label in [('width',tr('底面の横幅','Base Width')),('depth',tr('底面の縦高さ','Base Height')),('height',tr('ドームの高さ','Dome Height')),('thickness',tr('肉厚（0＝中実）','Wall (0 = solid)')),('diameter',tr('直径','Diameter')),('section',tr('断面直径','Section Diameter')),
                          ('growth',tr('1巻きの半径増分','Radial Growth per Turn')),('pitch',tr('ピッチ','Pitch')),('turns',tr('巻き数','Turns')),('taper_angle',tr('テーパー角度','Taper Angle')),
                          ('wall',tr('肉厚（0＝中実）','Wall Thickness (0 = solid)')),('length',tr('長さ','Length')),('path_fraction',tr('経路の弧長割合','Path Arc-length Fraction')),('backward_fraction',tr('逆方向の弧長割合（閉経路）','Backward Arc-length Fraction (Closed Path)'))]:
            field(key,label,self.spin())
        for key in ('width','depth','height'):self.fields[key].setRange(.01,100000)
        self.fields['thickness'].setRange(0,100000)
        self.fields['wall'].setRange(0,100000)
        self.fields['path_fraction'].setRange(.001,1);self.fields['path_fraction'].setDecimals(8);self.fields['path_fraction'].setSingleStep(.05)
        self.fields['backward_fraction'].setRange(0,1);self.fields['backward_fraction'].setDecimals(8);self.fields['backward_fraction'].setSingleStep(.05)
        self.fields['taper_angle'].setRange(-45,45);self.fields['taper_angle'].setSuffix('°')
        self.fields['turns'].setSuffix('');self.fields['turns'].setRange(.25,50);self.fields['turns'].setSingleStep(.25)
        self.left=field('left',tr('巻き方向','Winding'),W.QComboBox())
        self.left.addItem(tr('右巻き','Right-handed'),False);self.left.addItem(tr('左巻き','Left-handed'),True)
        self.section_kind=field('section_kind',tr('断面の形状','Section Shape'),W.QComboBox())
        for ja,en,key in [('円形','Circular','circular'),('正方形','Square','square'),('正三角形（外向き）','Triangle (outward)','triangle_out'),('正三角形（内向き）','Triangle (inward)','triangle_in')]:
            self.section_kind.addItem(tr(ja,en),key)
        coil_input_ui.build(self,field)
        self.axis=field('axis',tr('軸方向','Axis'),W.QComboBox())
        for axis in ('Z','X','Y'):self.axis.addItem(axis,axis)
        for key in ('x','y','z'):
            spin=field(key,tr('位置 ','Position ')+key.upper(),self.spin());spin.setRange(-100000,100000)
        self.note=W.QLabel();self.note.setWordWrap(True);form.addRow(self.note)
        self.combos=(self.path,self.left,self.section_kind,self.coil_mode_combo,self.axis)
        self.spins=tuple(w for w in self.fields.values() if isinstance(w,W.QDoubleSpinBox))
        self.cache_key=None;self.cache_shape=None

    def start(self,kind=None,existing=None):
        self.cancel()
        if self.ws.current_sketch():raise ValueError(tr('先にスケッチ編集を終了してください。','Finish editing the sketch first.'))
        self.kind=existing.FluxPrimitive if existing else kind
        if self.kind not in primitives.KINDS:raise ValueError('Unknown primitive')
        self.preferred_height={'dome':500,'sphere':330,'torus':410,'coil':650,'spiral':600,'pipe':460}[self.kind]
        self.section_kind.clear()
        options=[('円形','Circular','circular'),('正方形','Square','square'),('正三角形','Triangle','triangle')] if self.kind=='pipe' else [('円形','Circular','circular'),('正方形','Square','square'),('正三角形（外向き）','Triangle (outward)','triangle_out'),('正三角形（内向き）','Triangle (inward)','triangle_in')]
        for ja,en,key in options:self.section_kind.addItem(tr(ja,en),key)
        self.doc=self.ws.doc();self.existing=existing
        self.selection=[(s.ObjectName,tuple(s.SubElementNames)) for s in Gui.Selection.getSelectionEx()]
        values=primitives.settings(existing) if existing else primitives.defaults(self.kind)
        self.heading.setText(primitives.title(self.kind)+(tr('を編集',' — Edit') if existing else ''))
        self.path.clear();self.path.addItem(tr('直線（長さを指定）','Straight (specify length)'),None)
        if self.kind=='pipe':
            selected=Gui.Selection.getSelection()
            paths=[]
            for obj in self.doc.Objects:
                if getattr(obj,'FluxCADInternal',False) or not hasattr(obj,'Shape'):continue
                try:primitives.check_path(self.doc,obj,existing);paths.append(obj)
                except Exception:continue
            for obj in paths:self.path.addItem(obj.Label,obj.Name)
            source=values['path'] if existing else next((o for o in selected if o in paths),None)
            if source:self.path.setCurrentIndex(self.path.findData(source.Name))
            elif existing and existing.UsePath:
                self.path.addItem(tr('経路がありません — 選び直してください','Missing path — select a replacement'),'__missing__')
                self.path.setCurrentIndex(self.path.count()-1)
        for key,value in values.items():
            if key in ('left','path','section_kind'):continue
            self.fields[key].setValue(value)
        primitive_precision.lock_dimensions(existing,self.kind,self.fields)
        if self.kind=='dome':
            import model_dome
            model_dome.lock_fields(existing,self.fields)
        self.section_kind.setCurrentIndex(max(0,self.section_kind.findData(values.get('section_kind','circular'))))
        self.left.setCurrentIndex(1 if values.get('left') else 0);self.axis.setCurrentIndex(0)
        base=existing.Placement.Base if existing else App.Vector()
        for key,value in zip(('x','y','z'),base):self.fields[key].setValue(value)
        if self.kind=='dome':primitives.model_dome.remember_editor(self.fields)
        else:primitive_precision.remember(self.fields)
        coil_input_ui.begin(self,values)
        self.ws.region_picker.ticket+=1;self.ws.region_picker.clear()
        self.cache_key=None;self.active=True;self.panel.show();self.update_preview();self.position()

    def parameters(self):
        primitive_precision.lock_position(self.existing,self.fields)
        result={k:self.fields[k].value() for k in primitives.defaults(self.kind) if k not in ('path','left','section_kind')}
        if self.kind in ('coil','spiral'):result.update(left=self.left.currentData(),section_kind=self.section_kind.currentData())
        if self.kind=='pipe':
            result['section_kind']=self.section_kind.currentData()
            name=self.path.currentData()
            result['path']=self.doc.getObject(name) if name else None
            if not name:result['path_fraction']=1;result['backward_fraction']=0
            if name and result['path'] is None:raise ValueError(tr('経路が削除されています。','The path has been deleted.'))
        if self.kind=='dome':result=primitives.model_dome.editor_values(self.existing,self.fields,result)
        else:
            primitive_precision.lock_dimensions(self.existing,self.kind,self.fields)
            result=primitive_precision.values(self.existing,self.fields,result)
        return coil_input_ui.apply(self,result)

    def pose(self):
        primitive_precision.lock_position(self.existing,self.fields)
        position=tuple(self.fields[k].value() for k in ('x','y','z'))
        if self.existing:
            if self.kind=='dome':position=primitives.model_dome.editor_position(self.existing,self.fields,position)
            else:position=primitive_precision.position(self.existing,self.fields,position)
            result=App.Placement(self.existing.Placement);result.Base=App.Vector(*position);return result
        return primitives.placement(position,'Z' if self.kind=='pipe' and self.path.currentData() else self.axis.currentData())

    def signature(self):
        values=self.parameters();path=values.get('path')
        return (tuple((k,v) for k,v in values.items() if k!='path'),
                (path.Name,path.Shape.hashCode(),str(path.getGlobalPlacement()),primitives.pipe_path_guard.stamp(path)) if path else None,
                str(self.existing.getGlobalPlacement()) if self.existing else None)

    def visible_fields(self):
        path_mode=self.kind=='pipe' and self.path.currentData() is not None
        keys=set(primitives.defaults(self.kind))|{'x','y','z'}
        if not self.existing and self.kind!='sphere' and not path_mode:keys.add('axis')
        if path_mode:keys.discard('length')
        else:keys.discard('path_fraction');keys.discard('backward_fraction')
        keys=coil_input_ui.visible_keys(self,keys)
        self.labels['height'].setText(tr('中心線の高さ','Centerline Height') if self.kind=='coil' else tr('ドームの高さ','Dome Height'))
        for key,widget in self.fields.items():widget.setVisible(key in keys);self.labels[key].setVisible(key in keys)
        self.labels['diameter'].setText(tr('中心径','Centerline Diameter') if self.kind in ('torus','coil','spiral') else tr('外径','Outside Diameter') if self.kind=='pipe' else tr('直径','Diameter'))
        if self.kind=='pipe' and self.section_kind.currentData()!='circular':self.labels['diameter'].setText(tr('断面の辺長','Section Side Length'))
        self.labels['section'].setText(tr('断面の辺長','Section Side Length') if self.kind in ('coil','spiral') and self.section_kind.currentData()!='circular' else tr('線径','Wire Diameter') if self.kind in ('coil','spiral') else tr('断面直径','Section Diameter'))
        for key in ('x','y','z'):self.labels[key].setText((tr('オフセット ','Offset ') if path_mode else tr('位置 ','Position '))+key.upper())
        self.note.setText(dict(spiral=tr('XY平面内で外向きに巻く実体です。中心径は始端の断面重心径、半径増分は1巻きごとの増加です。','Creates an outward planar spiral solid. Diameter is the starting section-centroid diameter; growth is radial increase per turn.'),dome=primitives.model_dome.note(),sphere=tr('中心位置と直径を指定します。','Specify the center and diameter.'),
            torus=tr('中心径は管の中心を通る円の直径です。外径 = 中心径 + 断面直径。','Centerline diameter is measured through the tube center. Outside diameter = centerline + section diameter.'),
            coil=tr('円形・正方形・正三角形の断面を中心線に直交させて巻きます。中心径は断面重心の軌道径です。高さ = ピッチ × 巻き数。テーパーは正で拡大、負で縮小します。中心径は始端の径です。','Sweeps a circular, square or equilateral triangular section normal to the centerline. Diameter measures the section-centroid path. Height = pitch × turns. Positive taper expands, negative contracts; diameter is measured at the start.'),
            pipe=tr('経路には輪郭が1つにつながったスケッチを選びます。直線なら長さを指定できます。円形は外径、正方形・正三角形は辺長を指定します。肉厚0で中実、正で中空です。断面は原本の座標軸を基準に向きを決めます。経路の弧長割合.001～1で始端からの長さを指定し、閉経路は継ぎ目を始端とします。閉経路のみ逆方向割合0または.001～1を追加でき、両方向の合計は1以下です。合計1は全周です。断面の向きは新しい始端で決まります。','Select a sketch containing one connected path, or specify a straight length. Size is outside diameter for circles and side length for squares/triangles. Wall0 is solid;positive wall is hollow. Section orientation uses the source coordinate axes. Path arc-length fraction .001–1 starts at the native path origin/seam;1 uses the full path. Closed paths also accept backward fraction0 or .001–1;the sum must be at most1. Sum1 uses the full closed path. Section orientation is defined at the new start.'))[self.kind])


    def update_preview(self):
        self.timer.stop()
        if not self.active:return
        if App.ActiveDocument!=self.doc:self.cancel();return
        self.clear_preview();self.valid=False;self.accept_button.setEnabled(False);self.visible_fields()
        try:
            values=self.parameters();signature=self.signature()
            if self.kind=='dome':
                hint=primitives.model_dome.thickness_hint(values)
                if hint:self.note.setText(self.note.text()+'\n'+hint)
            if self.kind=='pipe':primitives.check_path(self.doc,values['path'],self.existing)
            key=(self.kind,signature[:2])
            if key!=self.cache_key:
                self.cache_shape=primitives.shape(self.kind,**values);self.cache_key=key
            shape=self.cache_shape.copy();pose=self.pose()
            primitive_precision.check_placement(self.existing,pose)
            if self.existing:pose=self.existing.getGlobalPlacement().multiply(self.existing.Placement.inverse()).multiply(pose)
            shape.Placement=pose.multiply(shape.Placement)
            self.show_shape(shape,'new')
            if self.kind=='dome':
                volume_note=primitives.model_dome.material_volume_note(shape)
                if volume_note:self.note.setText(self.note.text()+'\n'+volume_note)
            if self.existing:self.hidden.append((self.existing,self.existing.Visibility));self.existing.Visibility=False
            self.status.setText(tr('新規ボディとして作成します。','Creates a new body.') if not self.existing else tr('寸法と位置を更新します。','Updates dimensions and position.'))
            if self.kind=='coil':self.status.setText(self.status.text()+tr('\n中心線の高さ: %.3f mm','\nCenterline height: %.3f mm')%(values['pitch']*values['turns']))
            self.status.setStyleSheet('color:#3c6f62;');self.valid=True;self.accept_button.setEnabled(True)
            self.last_signature=signature
        except Exception as error:self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;')

    def accept(self):
        if not self.active:return
        for spin in self.spins:spin.interpretText()
        self.update_preview()
        if not self.valid:return
        if (self.kind!='dome' and primitive_precision.unchanged(self.existing,self.parameters(),self.pose())) or (self.kind=='dome' and primitive_precision.unchanged_dome(self.existing,self.parameters(),self.pose())):
            self.cancel();self.ws.refresh();return
        try:
            self.clear_preview()
            obj=primitives.create(self.doc,self.kind,existing=self.existing,pose=self.pose(),**self.parameters())
        except Exception as error:
            self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;');return
        self.active=False;self.timer.stop();self.panel.hide();self.ws.region_picker.clear()
        Gui.Selection.clearSelection();Gui.Selection.addSelection(obj);self.ws.refresh()

    def refresh(self):
        if not self.active:
            return
        try:
            if App.ActiveDocument != self.doc or self.ws.current_sketch() or (self.existing and not self.existing.Document):
                self.cancel()
                return
            if self.existing:
                name = self.existing.Name
                if not isinstance(name, str) or self.doc.getObject(name) != self.existing:
                    self.cancel()
                    return
            if self.signature() != getattr(self, 'last_signature', None):
                self.update_preview()
        except (RuntimeError, ReferenceError):
            self.cancel()
            return
        except ValueError as error:
            self.clear_preview()
            self.valid = False
            self.accept_button.setEnabled(False)
            self.status.setText(str(error))
        self.position()
