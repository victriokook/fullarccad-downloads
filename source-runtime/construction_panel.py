from panel_focus import hide_modeling_panel
"""Movable construction-plane preview with native face, edge and vertex picking."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets as W
from pivy import coin
from floating_panel import FloatingPanel
from i18n import tr
import model_construction as planes


class ConstructionPanel(FloatingPanel):
    layout_key='ConstructionPanel'
    preferred_height=450

    def __init__(self,ws):
        self.ticket=0;self.picking=None;self.observing=False
        super().__init__(ws)
        policy=self.status.sizePolicy();policy.setHeightForWidth(True);self.status.setSizePolicy(policy)

    def build_fields(self,form):
        form.setRowWrapPolicy(W.QFormLayout.WrapLongRows)
        self.base=W.QComboBox()
        for label,key in [('XY','XY'),('XZ','XZ'),('YZ','YZ'),(tr('選択した面','Selected Face'),'face')]:self.base.addItem(label,key)
        self.base_label=W.QLabel(tr('基準平面','Reference Plane'));form.addRow(self.base_label,self.base)
        self.a_button=W.QPushButton();self.b_button=W.QPushButton();self.c_button=W.QPushButton();self.axis_button=W.QPushButton()
        form.addRow(self.a_button);form.addRow(self.b_button);form.addRow(self.c_button)
        self.path_all_button=W.QPushButton(tr('経路全体を使用','Use Entire Path'));self.path_all_button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(self.use_entire_path));form.addRow(self.path_all_button)
        self.path_mode=W.QComboBox();self.path_mode.addItem(tr('比率','Proportional'),'fraction');self.path_mode.addItem(tr('距離','Distance'),'distance');self.path_mode.addItem(tr('参照頂点まで（直線辺）','To Vertex (Straight Edge)'),'to_object')
        self.path_mode_label=W.QLabel(tr('位置の指定','Position Mode'));form.addRow(self.path_mode_label,self.path_mode)
        self.fraction=self.spin();self.fraction.setRange(0,100);self.fraction.setDecimals(6);self.fraction.setSuffix(' %');self.fraction.setValue(50)
        self.fraction_label=W.QLabel(tr('位置','Position'));form.addRow(self.fraction_label,self.fraction)
        self.path_distance=self.spin();self.path_distance.setRange(0,1000000);self.path_distance.setDecimals(6);self.path_distance.setValue(10)
        self.path_distance_label=W.QLabel(tr('経路上の距離','Distance Along Path'));form.addRow(self.path_distance_label,self.path_distance)
        self.path_object_offset=self.spin();self.path_object_offset.setRange(-1000000,1000000);self.path_object_offset.setDecimals(8)
        self.path_object_offset_label=W.QLabel(tr('参照頂点からの経路方向距離','Offset from Vertex Along Path'));form.addRow(self.path_object_offset_label,self.path_object_offset)
        self.path_extend=W.QCheckBox(tr('端点の接線方向へ延長','Extend Along Endpoint Tangent'));self.path_extend.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.schedule));form.addRow(self.path_extend)
        self.path_reverse=W.QCheckBox(tr('終点から測る','Measure from End'));self.path_reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.schedule));form.addRow(self.path_reverse)
        self.axis=W.QComboBox()
        for label,key in [('X','X'),('Y','Y'),('Z','Z'),(tr('選択した直線辺','Selected Straight Edge'),'edge')]:self.axis.addItem(label,key)
        self.axis_label=W.QLabel(tr('回転軸','Rotation Axis'));form.addRow(self.axis_label,self.axis);form.addRow(self.axis_button)
        self.angle=self.spin();self.angle.setRange(-180,180);self.angle.setValue(45);self.angle.setSuffix(' °')
        self.angle_label=W.QLabel(tr('角度','Angle'));form.addRow(self.angle_label,self.angle)
        self.distance=self.spin();self.distance.setRange(-1000000,1000000);self.distance.setDecimals(6);self.distance.setValue(10)
        self.offset_label=W.QLabel(tr('距離','Distance'));form.addRow(self.offset_label,self.distance)
        self.perpendicular_direction=W.QComboBox();self.perpendicular_direction.addItem(tr('U方向を含む','Contains U Direction'),'u');self.perpendicular_direction.addItem(tr('V方向を含む','Contains V Direction'),'v')
        self.perpendicular_direction_label=W.QLabel(tr('面内方向','Face Direction'));form.addRow(self.perpendicular_direction_label,self.perpendicular_direction)
        self.perpendicular_offset=self.spin();self.perpendicular_offset.setRange(-1000000,1000000);self.perpendicular_offset.setDecimals(8)
        self.perpendicular_offset_label=W.QLabel(tr('頂点からの距離','Offset from Vertex'));form.addRow(self.perpendicular_offset_label,self.perpendicular_offset)
        self.tangent_reference=W.QCheckBox(tr('平面を角度の基準にする（円柱・円すい）','Measure Angle from Planar Face (Cylinder/Cone)'));self.tangent_reference.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.schedule));form.addRow(self.tangent_reference)
        self.reverse=W.QCheckBox(tr('法線を反転','Flip Normal'));self.reverse.toggled.connect(__import__('builtins')._fullarc_qt_slot(self.schedule));form.addRow(self.reverse)
        self.size=self.spin();self.size.setRange(.1,1000000);self.size.setValue(80)
        form.addRow(tr('表示サイズ','Display Size'),self.size)
        self.note=W.QLabel();self.note.setWordWrap(True);form.addRow(self.note)
        for widget in (self.base,self.axis,self.angle,self.distance,self.size,self.a_button,self.b_button,self.c_button,self.axis_button,self.path_all_button,self.path_mode,self.fraction,self.path_distance):widget.setSizePolicy(W.QSizePolicy.Ignored,W.QSizePolicy.Fixed)
        policy=W.QSizePolicy(W.QSizePolicy.Ignored,W.QSizePolicy.Minimum);policy.setHeightForWidth(True);self.note.setSizePolicy(policy)
        for button,key in [(self.a_button,'reference_a'),(self.b_button,'reference_b'),(self.c_button,'reference_c'),(self.axis_button,'axis_reference')]:button.clicked[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False,k=key:self.begin_pick(k),(2, 0, False, False)))
        self.combos=(self.base,self.axis,self.path_mode,self.perpendicular_direction);self.spins=(self.angle,self.distance,self.size,self.fraction,self.path_distance,self.path_object_offset,self.perpendicular_offset)

    def start(self,kind='midplane',existing=None):
        self.cancel()
        if self.ws.current_sketch():raise ValueError(tr('先にスケッチ編集を終了してください。','Finish editing the sketch first.'))
        self.kind=str(existing.FluxConstructionPlane) if existing else kind;self.existing=existing;self.doc=self.ws.doc()
        self.selection=[(s.ObjectName,tuple(s.SubElementNames)) for s in Gui.Selection.getSelectionEx()]
        values=planes.settings(existing) if existing else dict(base='XY',axis='X',angle=0 if self.kind in ('tangent','along_path','tangent_point') else 45,size=80)
        values.setdefault('offset',0 if self.kind=='two_edges' else 10)
        if self.kind=='tangent':values['offset']=values.get('tangent_offset',0.)
        for key,value in dict(path_mode='fraction',fraction=.5,path_distance=10,path_reverse=False,path_extend=False,path_object_offset=0.).items():values.setdefault(key,value)
        values.setdefault('tangent_reference',False)
        values.setdefault('perpendicular_direction','u');values.setdefault('perpendicular_offset',0.)
        self.refs={key:values.get(key) for key in ('reference_a','reference_b','reference_c','axis_reference')}
        if not existing:
            faces=[];edges=[];vertices=[];face_points=[];paths=[]
            for item in Gui.Selection.getSelectionEx():
                for index,sub in enumerate(item.SubElementNames or ('',)):
                    try:
                        ref=planes.resolve(self.doc,item.ObjectName,sub)
                        if self.kind=='along_path' and (not ref[1] or ref[1].startswith('Edge')):paths.append(ref)
                        if ref[1].startswith('Face'):
                            if self.kind not in ('offset','tangent','tangent_point','perpendicular_point'):planes.face(ref)
                            faces.append(ref)
                            picked=getattr(item,'PickedPoints',[]);face_points.append(picked[index] if index<len(picked) else None)
                        elif ref[1].startswith('Edge'):planes.edge(ref);edges.append(ref)
                        elif ref[1].startswith('Vertex'):planes.vertex(ref);vertices.append(ref)
                    except Exception:continue
            if faces:self.refs['reference_a']=faces[0]
            if self.kind in ('tangent_point','offset_point','perpendicular_point'):
                self.refs['reference_a']=faces[0] if faces else None;self.refs['reference_b']=vertices[0] if vertices else None
            if self.kind=='two_edges':
                self.refs['reference_a']=edges[0] if edges else None;self.refs['reference_b']=edges[1] if len(edges)>1 else None
            if self.kind=='midplane' and len(faces)>1:self.refs['reference_b']=faces[1]
            if self.kind in ('angle','offset'):
                if faces:values['base']='face'
                if self.kind=='angle' and edges:values['axis']='edge';self.refs['axis_reference']=edges[0]
            if self.kind=='three_points':
                for index,key in enumerate(('reference_a','reference_b','reference_c')):self.refs[key]=vertices[index] if len(vertices)>index else None
            if self.kind=='tangent' and faces:
                try:values['angle']=planes.tangent_angle(faces[0],face_points[0])
                except ValueError:pass
            if self.kind=='along_path':self.refs['reference_a']=paths[0] if paths else None
        self.base.setCurrentIndex(self.base.findData(values['base']));self.axis.setCurrentIndex(self.axis.findData(values['axis']))
        self.angle.setValue(values['angle']);self.size.setValue(values['size']);self.distance.setValue(values['offset'])
        self.reverse.setChecked(values.get('reversed',False));self.tangent_reference.setChecked(values['tangent_reference'])
        self.path_mode.setCurrentIndex(self.path_mode.findData(values['path_mode']));self.fraction.setValue(values['fraction']*100)
        self.path_distance.setValue(values['path_distance']);self.path_reverse.setChecked(values['path_reverse']);self.path_extend.setChecked(values['path_extend']);self.path_object_offset.setValue(values['path_object_offset'])
        self.perpendicular_direction.setCurrentIndex(self.perpendicular_direction.findData(values['perpendicular_direction']));self.perpendicular_offset.setValue(values['perpendicular_offset'])
        self.original_values=values;self.original_display={'angle':self.angle.value(),'size':self.size.value(),'offset':self.distance.value(),'fraction':self.fraction.value()/100,'path_distance':self.path_distance.value(),'path_object_offset':self.path_object_offset.value(),'perpendicular_offset':self.perpendicular_offset.value()}
        self.heading.setText(planes.title(self.kind)+(tr('を編集',' — Edit') if existing else ''))
        self.note.setText(tr('平面を2つ選びます。非平行の場合は法線の近い向きをそろえた和の二等分面を作ります。もう一方の二等分面は未対応です。直角での選択と法線軸の切替付近では向きが切り替わる場合があります。参照変更に追従し、表示サイズは原点に影響しません。作成後の原本の所属・面構成変更は対象外です。',
                            'Select two planar faces. Nonparallel inputs use the summed,hemisphere-aligned canonical normals; the alternate bisector is excluded. The choice can switch at right angles or canonical-axis transitions. References are linked; display size does not move the origin. Reparenting sources or changing face topology after creation is excluded.') if self.kind=='midplane' else
                          tr('基準平面上の直線辺または軸を中心に回転します。軸の向きに対して角度の正負で傾く側を切り替えます。',
                             'Rotate about a straight edge or axis in the reference plane. Positive and negative angles tilt to opposite sides of the axis.'))
        if self.kind=='offset':self.note.setText(tr('基準面から垂直に距離を指定します。緑の矢印が正方向です。負の距離で反対側へ作成できます。表示サイズを変えてもスケッチの原点は動きません。',
            'Enter the perpendicular distance from the reference plane. The green arrow points in the positive direction. Use a negative distance for the opposite side. Display size does not move the sketch origin.'))
        if self.kind=='three_points':self.note.setText(tr('頂点やスケッチの端点を3つ選びます。点1が原点、点1→点2がX方向になります。一直線上の3点は使えません。緑の矢印が面の正方向です。',
            'Select three vertices or sketch endpoints. Point 1 is the origin; Point 1 to Point 2 defines X. Collinear points cannot define a plane. The green arrow is the positive normal.'))
        if self.kind=='tangent':self.note.setText(tr('円柱または円すいの側面を選びます。クリックした位置から角度を調整できます。角度は選択面の基準方向から測ります。距離0は接平面、非ゼロは平行な平面です。緑の矢印（反転後）が距離の正方向です。',
            'Select a cylindrical or conical side face. Adjust the angle from the clicked position. Angles are measured from the face\'s reference direction. Zero distance is tangent;nonzero creates a parallel plane. Positive distance follows the green arrow after Flip Normal.'))
        if self.kind=='along_path':self.note.setText(tr('辺をクリックし、位置を比率または距離で指定します。「経路全体を使用」でつながったスケッチ全体を使えます。青いSが測定の始点、緑の矢印が平面の正方向です。距離指定で延長をオンにすると、開経路の終端を越えて接線方向に配置できます。反対側は「終点から測る」を使います。閉経路の外側・負の距離・曲線そのものの外挿には対応しません。「参照頂点まで」は直線EdgeとVertexを指定し、直線への投影位置に平面を置きます。距離0は頂点を通り、距離の正方向は測定方向です。',
            'Click an edge and set its position by proportion or distance. Use Entire Path selects the connected sketch. Blue S marks the measuring start; the green arrow is the plane normal. Enable extension in Distance mode to continue beyond an open path endpoint along its tangent. Measure from End extends the opposite end. No closed-path extension,negative distance or analytic curve extrapolation. To Vertex uses one straight Edge and explicit Vertex projected onto its supporting line. Zero offset passes through the vertex;positive offset follows the measurement direction.'))
        if self.kind=='two_edges':self.note.setText(tr('非平行で同一平面上にある直線辺を2本選択します。延長した交点が原点です。平行・ねじれ位置・曲線辺は使えません。','Select two nonparallel coplanar straight edges. Their extended intersection is the origin. Parallel, skew and curved edges are excluded.'))
        if self.kind=='tangent_point':self.note.setText(tr('平面・解析曲面・Bスプライン面・ベジェ面と、その有限面上の頂点を選択します。頂点が平面の原点になります。面外点・穴内部・特異点・円すい頂点から0.000001mm以内は対象外です。','Select a planar, analytical, B-spline or Bezier face and a vertex on its bounded surface. The vertex is the plane origin. Off-face points, holes, singular freeform faces and points within0.000001mm of the cone apex are excluded.'));self.note.setText(self.note.text()+tr(' 自由曲面は各方向2～50制御点、次数1～9です。',' Freeform:2–50 poles per direction, degree1–9.'))
        if self.kind=='offset_point':self.note.setText(tr('平面の面と、通過する頂点を選択します。頂点の移動で距離が更新されます。原点は基準平面の原点から法線方向に移動し、頂点の面内位置には追従しません。','Select a planar face and a vertex the plane passes through. Moving the vertex updates the offset. The origin moves normally from the base-plane origin; in-plane vertex motion does not move the origin.'))
        if self.kind=='perpendicular_point':self.note.setText(tr('平面は任意のVertex、円柱・円すい・トーラスは面上のVertexを指定します。面のU/V接線と法線を含む垂直平面です。距離0は頂点を通り、正方向は反転後の緑の法線です。円すい頂点・球・自由曲面・自動スナップは対象外です。Autodeskとの符号・面内軸一致は保証しません。','Use any Vertex for a planar Face,or an on-face Vertex for cylinder/cone/torus. The plane contains the native U/V tangent and surface normal. Zero offset passes through the vertex;positive offset follows the flipped green normal. Cone apex,spheres,freeform and automatic snaps are excluded. Identical Autodesk signs/frames are not guaranteed.'))
        if self.kind=='tangent':self.note.setText(self.note.text()+tr(' 基準平面を使う場合は円柱・円すい側面と軸に平行な平面を選びます。角度は基準面の向き付き法線からnative軸回りに測ります。円すいは有限面中間位置の半径で角度を求めます。面の反転で接する側が変わります。傾いた基準面は対象外です。',' Reference mode requires a cylindrical/conical side face and planar face parallel to its axis. Angle rotates the oriented reference normal about the native axis. Cone angle probes use the mid-face radius. Reversing the reference face changes the tangent side. Tilted reference planes are excluded.'))
        self.ws.region_picker.ticket+=1;self.ws.region_picker.clear()
        Gui.Selection.addObserver(self);self.observing=True;self.active=True;self.panel.show()
        if self.kind in ('midplane','two_edges','tangent_point','offset_point','perpendicular_point') and not self.refs['reference_a']:self.picking='reference_a'
        elif self.kind in ('midplane','two_edges','tangent_point','offset_point','perpendicular_point') and not self.refs['reference_b']:self.picking='reference_b'
        elif self.kind=='three_points':self.picking=next((key for key in ('reference_a','reference_b','reference_c') if not self.refs[key]),None)
        elif self.kind in ('tangent','along_path','tangent_point') and not self.refs['reference_a']:self.picking='reference_a'
        self.update_preview();self.position()

    def parameters(self):
        values=dict(self.refs,base=self.base.currentData(),axis=self.axis.currentData(),angle=self.angle.value(),size=self.size.value(),offset=self.distance.value(),reversed=self.reverse.isChecked(),path_mode=self.path_mode.currentData(),fraction=self.fraction.value()/100,path_distance=self.path_distance.value(),path_reverse=self.path_reverse.isChecked(),path_object_offset=self.path_object_offset.value())
        if self.existing:
            for key in ('angle','size','offset','fraction','path_distance','path_object_offset'):
                if values[key]==self.original_display[key]:values[key]=self.original_values[key]
        if self.kind=='perpendicular_point':
            values['perpendicular_direction']=self.perpendicular_direction.currentData();values['perpendicular_offset']=self.perpendicular_offset.value()
            if self.existing and values['perpendicular_offset']==self.original_display['perpendicular_offset']:values['perpendicular_offset']=self.original_values['perpendicular_offset']
        if self.kind=='along_path':values['path_extend']=self.path_extend.isChecked()
        if self.kind=='tangent':values['tangent_offset']=values['offset'];values['tangent_reference']=self.tangent_reference.isChecked()
        return values

    def use_entire_path(self):
        if not self.active or self.kind!='along_path' or not self.refs['reference_a']:return
        try:
            ref=(self.refs['reference_a'][0],'');planes.path_curve(ref)
            self.refs['reference_a']=ref;self.ticket+=1;self.picking=None;Gui.Selection.clearSelection();self.update_preview()
        except Exception as error:self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;')

    def begin_pick(self,key):
        if not self.active:return
        self.ticket+=1;self.picking=key;Gui.Selection.clearSelection();self.update_preview()

    def addSelection(self,docname,objname,subname,point):
        if not self.active or not self.picking or docname!=self.doc.Name:return
        ticket=self.ticket;key=self.picking
        def receive():
            if not self.active or self.picking!=key or self.ticket!=ticket:return
            try:
                ref=planes.resolve(self.doc,objname,subname)
                (planes.vertex if self.kind=='along_path' and key=='reference_b' else planes.path_curve if self.kind=='along_path' else planes.face if self.kind=='tangent' and key=='reference_b' else planes.round_face if self.kind=='tangent' else planes.vertex if self.kind=='three_points' or (self.kind in ('tangent_point','offset_point','perpendicular_point') and key=='reference_b') else planes.edge if key=='axis_reference' or self.kind=='two_edges' else (__import__('builtins')._fullarc_qt_slot(lambda ref:planes.element(ref,'Face'),(1, 1, False, False))) if self.kind in ('tangent_point','perpendicular_point') else planes.face)(ref)
                # Check this reference alone, even when the other is not selected yet.
                if ref[0].Document!=self.doc or (self.existing and (ref[0]==self.existing or self.existing in ref[0].OutListRecursive)):
                    raise ValueError(tr('この平面自身や後続の加工は参照できません。','Cannot reference this plane or its descendants.'))
                if self.kind=='three_points':
                    values=dict(self.refs);values[key]=ref
                    refs=[values[k] for k in ('reference_a','reference_b','reference_c')]
                    for other_key,other in self.refs.items():
                        if other_key!=key and other_key!='axis_reference' and other and (planes.vertex(other)-planes.vertex(ref)).Length<1e-7:
                            raise ValueError(tr('位置の異なる3つの点を選択してください。','Select three points at different positions.'))
                    if all(refs):planes.points_frame(*refs)
                self.refs[key]=ref;self.ticket+=1;self.picking=None
                if self.kind=='tangent' and key=='reference_a' and not self.tangent_reference.isChecked():self.angle.setValue(planes.tangent_angle(ref,point))
                if self.kind in ('midplane','two_edges','tangent_point','offset_point','perpendicular_point') and key=='reference_a' and not self.refs['reference_b']:self.picking='reference_b'
                elif self.kind=='three_points':self.picking=next((k for k in ('reference_a','reference_b','reference_c') if not self.refs[k]),None)
                Gui.Selection.clearSelection();self.update_preview()
            except Exception as error:
                self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;');Gui.Selection.clearSelection()
        QtCore.QTimer.singleShot(0,__import__('builtins')._fullarc_qt_slot(receive))

    def signature(self):
        refs=[]
        for ref in planes.references(self.kind,**self.parameters()):
            obj=ref[0] if ref else None
            refs.append((obj.Name,ref[1],obj.Shape.hashCode(),str(obj.getGlobalPlacement()),str(getattr(obj,'Error',''))) if obj else None)
        return str(refs),self.base.currentData(),self.axis.currentData(),self.angle.value(),self.size.value(),self.distance.value(),self.reverse.isChecked(),self.path_mode.currentData(),self.fraction.value(),self.path_distance.value(),self.path_reverse.isChecked(),self.path_extend.isChecked(),self.path_object_offset.value(),self.perpendicular_direction.currentData(),self.perpendicular_offset.value(),self.tangent_reference.isChecked(),self.picking

    def point_guide(self):
        points=[]
        for index,key in enumerate(('reference_a','reference_b','reference_c'),1):
            try:points.append((index,planes.vertex(self.refs[key])))
            except Exception:continue
        if not points:return
        if not self.overlay:
            root=coin.SoSeparator();pick=coin.SoPickStyle();pick.style=coin.SoPickStyle.UNPICKABLE;root.addChild(pick)
            graph=Gui.activeDocument().activeView().getSceneGraph();graph.addChild(root);self.overlay=(graph,root)
        node=coin.SoSeparator();self.overlay[1].addChild(node)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.15,.5,.8);material.transparency=0;node.addChild(material)
        style=coin.SoDrawStyle();style.pointSize=9;style.lineWidth=2;node.addChild(style)
        for index,point in points:
            marker=coin.SoSeparator();node.addChild(marker)
            coordinates=coin.SoCoordinate3();coordinates.point.setValue(tuple(point));marker.addChild(coordinates)
            dot=coin.SoPointSet();dot.numPoints=1;marker.addChild(dot)
            translation=coin.SoTranslation();translation.translation=tuple(point);marker.addChild(translation)
            font=coin.SoFont();font.size=16;marker.addChild(font)
            label=coin.SoText2();label.string=str(index);marker.addChild(label)
        if len(points)>1:
            path=[tuple(point) for index,point in points]
            if len(path)==3:path.append(path[0])
            coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(path),path);node.addChild(coordinates)
            line=coin.SoLineSet();line.numVertices.setValue(len(path));node.addChild(line)
        if self.valid:
            frame,center=planes.points_frame(self.refs['reference_a'],self.refs['reference_b'],self.refs['reference_c'],self.reverse.isChecked())
            normal=frame.Rotation.multVec(App.Vector(0,0,1));side=frame.Rotation.multVec(App.Vector(1,0,0));length=max(1,min(15,self.size.value()*.15))
            tip=center+normal*length
            path=[center,tip,tip-normal*length*.25+side*length*.12,tip,tip-normal*length*.25-side*length*.12]
            material=coin.SoMaterial();material.diffuseColor=(.16,.62,.4);material.transparency=0;node.addChild(material)
            coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(path),[tuple(v) for v in path]);node.addChild(coordinates)
            line=coin.SoLineSet();line.numVertices.setValue(len(path));node.addChild(line)

    def offset_guide(self):
        values=self.parameters();frame,center,normal=planes.offset_frame(values['base'],values['reference_a'])
        length=max(1,min(15,values['size']*.15));tip=center+normal*length
        side=frame.Rotation.multVec(App.Vector(1,0,0))
        points=[center,tip,tip-normal*length*.25+side*length*.12,tip,tip-normal*length*.25-side*length*.12]
        node=coin.SoSeparator();self.overlay[1].addChild(node)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.16,.62,.4);material.transparency=0;node.addChild(material)
        style=coin.SoDrawStyle();style.lineWidth=3;node.addChild(style)
        coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(points),[tuple(v) for v in points]);node.addChild(coordinates)
        line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line)

    def tangent_guide(self):
        values=self.parameters();frame,center=planes.tangent_frame(values['reference_a'],values['angle'],values['reversed'],values.get('reference_b'),values.get('tangent_reference',False))
        normal=frame.Rotation.multVec(App.Vector(0,0,1));side=frame.Rotation.multVec(App.Vector(1,0,0))
        center=center+normal*values['tangent_offset']
        length=max(1,min(15,values['size']*.15));tip=center+normal*length
        points=[center,tip,tip-normal*length*.25+side*length*.12,tip,tip-normal*length*.25-side*length*.12]
        node=coin.SoSeparator();self.overlay[1].addChild(node)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.16,.62,.4);material.transparency=0;node.addChild(material)
        style=coin.SoDrawStyle();style.lineWidth=3;style.pointSize=9;node.addChild(style)
        coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(points),[tuple(v) for v in points]);node.addChild(coordinates)
        line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line)
        dot=coin.SoPointSet();dot.numPoints=1;node.addChild(dot)

    def perpendicular_guide(self):
        values=self.parameters();frame,center=planes.perpendicular_point_frame(values['reference_a'],values['reference_b'],values['perpendicular_direction'],values['perpendicular_offset'],values['reversed'])
        normal=frame.Rotation.multVec(App.Vector(0,0,1));side=frame.Rotation.multVec(App.Vector(1,0,0))
        length=max(1,min(15,values['size']*.15));tip=center+normal*length
        points=[center,tip,tip-normal*length*.25+side*length*.12,tip,tip-normal*length*.25-side*length*.12]
        node=coin.SoSeparator();self.overlay[1].addChild(node)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.16,.62,.4);material.transparency=0;node.addChild(material)
        style=coin.SoDrawStyle();style.lineWidth=3;style.pointSize=9;node.addChild(style)
        coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(points),[tuple(v) for v in points]);node.addChild(coordinates)
        line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line)
        dot=coin.SoPointSet();dot.numPoints=1;node.addChild(dot)

    def path_guide(self):
        values=self.parameters();frame,curve,distance=planes.path_frame(values['reference_a'],values['path_mode'],values['fraction'],values['path_distance'],values['path_reverse'],values['angle'],values['reversed'],values.get('path_extend',False),values.get('reference_b'),values.get('path_object_offset',0))
        node=coin.SoSeparator();self.overlay[1].addChild(node)
        light=coin.SoLightModel();light.model=coin.SoLightModel.BASE_COLOR;node.addChild(light)
        material=coin.SoMaterial();material.diffuseColor=(.15,.5,.8);material.transparency=0;node.addChild(material)
        style=coin.SoDrawStyle();style.lineWidth=2;style.pointSize=8;node.addChild(style)
        stations=sorted(set([curve.length*i/64 for i in range(65)]+[curve.length-s if values['path_reverse'] else s for s in curve.ends]))
        path=[tuple(curve.at(s,values['path_reverse'])[0]) for s in stations]
        if distance<0 or distance>curve.length:path.append(tuple(frame.Base))
        coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(path),path);node.addChild(coordinates)
        line=coin.SoLineSet();line.numVertices.setValue(len(path));node.addChild(line)
        marker=coin.SoSeparator();node.addChild(marker);coordinates=coin.SoCoordinate3();coordinates.point.setValue(path[0]);marker.addChild(coordinates)
        dot=coin.SoPointSet();dot.numPoints=1;marker.addChild(dot)
        translation=coin.SoTranslation();translation.translation=path[0];marker.addChild(translation)
        font=coin.SoFont();font.size=16;marker.addChild(font);label=coin.SoText2();label.string='S';marker.addChild(label)
        normal=frame.Rotation.multVec(App.Vector(0,0,1));side=frame.Rotation.multVec(App.Vector(1,0,0));center=frame.Base
        length=max(1,min(15,values['size']*.15));tip=center+normal*length
        points=[center,tip,tip-normal*length*.25+side*length*.12,tip,tip-normal*length*.25-side*length*.12]
        material=coin.SoMaterial();material.diffuseColor=(.16,.62,.4);node.addChild(material)
        coordinates=coin.SoCoordinate3();coordinates.point.setValues(0,len(points),[tuple(v) for v in points]);node.addChild(coordinates)
        line=coin.SoLineSet();line.numVertices.setValue(len(points));node.addChild(line)
        dot=coin.SoPointSet();dot.numPoints=1;node.addChild(dot)
        return curve.length,distance

    def update_preview(self):
        self.timer.stop()
        if not self.active:return
        if App.ActiveDocument!=self.doc:self.cancel();return
        self.clear_preview();self.valid=False;self.accept_button.setEnabled(False)
        perpendicular=self.kind=='perpendicular_point'
        offsetpoint=self.kind=='offset_point';tangentpoint=self.kind in ('tangent_point','offset_point','perpendicular_point');twoedges=self.kind=='two_edges';angled=self.kind=='angle';mid=self.kind=='midplane';offset=self.kind=='offset';points=self.kind=='three_points';tangent=self.kind=='tangent';path=self.kind=='along_path'
        for widget in (self.perpendicular_direction,self.perpendicular_direction_label,self.perpendicular_offset,self.perpendicular_offset_label):widget.setVisible(perpendicular)
        for widget in (self.path_all_button,self.path_mode,self.path_mode_label,self.path_reverse):widget.setVisible(path)
        self.path_all_button.setEnabled(bool(self.refs['reference_a']) and bool(self.refs['reference_a'][1]))
        for widget in (self.fraction,self.fraction_label):widget.setVisible(path and self.path_mode.currentData()=='fraction')
        for widget in (self.path_distance,self.path_distance_label):widget.setVisible(path and self.path_mode.currentData()=='distance')
        self.path_extend.setVisible(path and self.path_mode.currentData()=='distance')
        path_object=path and self.path_mode.currentData()=='to_object'
        tangent_ref=tangent and self.tangent_reference.isChecked();self.tangent_reference.setVisible(tangent)
        self.path_all_button.setVisible(path and not path_object)
        for widget in (self.path_object_offset,self.path_object_offset_label):widget.setVisible(path_object)
        for widget in (self.base,self.base_label):widget.setVisible(not (mid or points or tangent or path or twoedges or tangentpoint))
        for widget in (self.axis,self.axis_label):widget.setVisible(angled)
        for widget in (self.angle,self.angle_label):widget.setVisible(angled or tangent or path or (tangentpoint and not offsetpoint and not perpendicular))
        self.angle_label.setText(tr('面内の回転','In-plane Rotation') if path or tangentpoint else tr('角度','Angle'))
        for widget in (self.distance,self.offset_label):widget.setVisible(offset or twoedges or tangent)
        self.offset_label.setText(tr('接平面からの距離','Offset from Tangent Plane') if tangent else tr('距離','Distance'))
        self.a_button.setVisible(tangentpoint or twoedges or mid or points or tangent or path or self.base.currentData()=='face');self.b_button.setVisible(tangentpoint or twoedges or mid or points or path_object or tangent_ref)
        self.c_button.setVisible(points);self.reverse.setVisible(tangentpoint or twoedges or points or tangent or path)
        self.axis_button.setVisible(angled and self.axis.currentData()=='edge')
        if ((self.picking=='reference_a' and not self.a_button.isVisible()) or
                (self.picking=='axis_reference' and not self.axis_button.isVisible())):
            self.ticket+=1;self.picking=None
        for button,key,label in [(self.a_button,'reference_a',tr('面','Face') if tangentpoint else tr('辺1','Edge 1') if twoedges else tr('経路','Path') if path else tr('曲面','Curved Face') if tangent else tr('点1','Point 1') if points else tr('面1','Face 1') if mid else tr('基準面','Reference Face')),
                                 (self.b_button,'reference_b',tr('角度の基準平面','Angle Reference Face') if tangent_ref else tr('参照頂点','Reference Vertex') if path_object else tr('通過する頂点','Through Vertex') if offsetpoint or perpendicular else tr('面上の頂点','Vertex on Face') if tangentpoint else tr('辺2','Edge 2') if twoedges else tr('点2','Point 2') if points else tr('面2','Face 2')),
                                 (self.c_button,'reference_c',tr('点3','Point 3')),(self.axis_button,'axis_reference',tr('軸の辺','Axis Edge'))]:
            ref=self.refs[key]
            try:description='%s / %s'%(ref[0].Label,ref[1] or tr('経路全体','Entire Path')) if ref and ref[0] else tr('選択','Select')
            except (ReferenceError,RuntimeError):description=tr('参照なし','Missing Reference')
            button.setText(label+': '+description);button.setToolTip(button.text());button.setStyleSheet('border:1px solid #258fbe;background:#e6f5ff;' if self.picking==key else '')
        try:
            values=self.parameters();planes.check_sources(self.doc,self.kind,self.existing,**values)
            shape=planes.build(self.kind,**values);self.show_shape(shape,'plane')
            if offset:self.offset_guide()
            if tangent:self.tangent_guide()
            if perpendicular:self.perpendicular_guide()
            if self.existing:self.hidden.append((self.existing,self.existing.Visibility));self.existing.Visibility=False
            self.status.setText(tr('この平面を選択して「スケッチを作成」で作図できます。','Select the finished plane and use Create Sketch to draw on it.'))
            if path:
                length,distance=self.path_guide();self.status.setText(tr('経路長: %.3f mm\n始点からの距離: %.3f mm\n確定後、平面を選んでスケッチを作成できます。','Path length: %.3f mm\nDistance from start: %.3f mm\nConfirm, then select the plane to create a sketch.')%(length,distance))
            self.status.setStyleSheet('color:#3c6f62;');self.valid=True;self.accept_button.setEnabled(not self.picking)
        except Exception as error:self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;')
        if points:self.point_guide()
        if self.picking:
            self.status.setText(tr('画面上の辺、またはブラウザーの経路スケッチを選択してください。','Click an edge in the view or select a path sketch in the browser.') if path else
                               tr('画面上の円柱または円すいの側面をクリックしてください。','Click a cylindrical or conical side face in the view.') if tangent else
                               tr('点%d：画面上の頂点またはスケッチの端点をクリックしてください。','Point %d: click a vertex or sketch endpoint in the view.')%(('reference_a','reference_b','reference_c').index(self.picking)+1) if points else
                               tr('画面上の直線辺をクリックしてください。','Click a straight edge in the view.') if self.picking=='axis_reference' else
                                tr('画面上の平らな面をクリックしてください。','Click a planar face in the view.'))
            self.status.setStyleSheet('color:#247c9c;')
        if self.picking and tangent_ref and self.picking=='reference_b':self.status.setText(tr('円柱の軸に平行な平らな面を選択してください。','Select a planar face parallel to the cylinder axis.'))
        if self.picking and path_object and self.picking=='reference_b':self.status.setText(tr('参照する頂点を選択してください。','Select the reference vertex.'))
        if self.picking and twoedges:self.status.setText(tr('直線辺%dを選択してください。','Select straight edge %d.')%(1 if self.picking=='reference_a' else 2))
        if self.picking and tangentpoint:self.status.setText(tr('面を選択してください。','Select a face.') if self.picking=='reference_a' else tr('その面上の頂点を選択してください。','Select a vertex on that face.'))
        if self.picking and perpendicular:self.status.setText(tr('平面の面を選択してください。','Select a planar face.') if self.picking=='reference_a' else tr('通過する頂点を選択してください。','Select the vertex to pass through.'))
        if self.picking and offsetpoint:self.status.setText(tr('平面の面を選択してください。','Select a planar face.') if self.picking=='reference_a' else tr('通過する頂点を選択してください。','Select the vertex to pass through.'))
        try:self.last_signature=self.signature()
        except (ReferenceError,RuntimeError):self.last_signature=None

    def detach(self):
        self.ticket+=1;self.picking=None
        if self.observing:Gui.Selection.removeObserver(self);self.observing=False

    def cancel(self):
        self.detach();super().cancel()

    def accept(self):
        if not self.active or self.picking:return
        for field in self.spins:field.interpretText()
        self.update_preview()
        if not self.valid:return
        try:
            self.clear_preview();result=planes.create(self.doc,self.kind,existing=self.existing,**self.parameters())
        except Exception as error:self.status.setText(str(error));self.status.setStyleSheet('color:#ac3830;');return
        self.detach();self.active=False;self.timer.stop();hide_modeling_panel(self);self.ws.region_picker.clear()
        Gui.Selection.clearSelection();Gui.Selection.addSelection(result);self.ws.refresh()

    def refresh(self):
        if not self.active:return
        try:
            if App.ActiveDocument!=self.doc or self.ws.current_sketch() or (self.existing and not self.existing.Document):self.cancel();return
            if self.signature()!=getattr(self,'last_signature',None):self.update_preview()
        except (ReferenceError,RuntimeError):self.cancel();return
        self.position()

    def eventFilter(self,widget,event):
        if self.active and self.picking and widget in self.widgets and event.type() in (QtCore.QEvent.MouseButtonPress,QtCore.QEvent.MouseButtonRelease,QtCore.QEvent.MouseButtonDblClick) and event.button()==QtCore.Qt.LeftButton:return False
        return super().eventFilter(widget,event)
