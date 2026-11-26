"""Dialogs for the bounded independent sheet prototype."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets as W
from i18n import tr
import independent_sheetmetal as core
import json
import math

def selected(kind):
    objects=Gui.Selection.getSelection()
    if len(objects)!=1:raise ValueError(tr('対象を1つ選択してください。','Select exactly one object.'))
    return core.owned(objects[0],kind)

def selected_base_edge(source):
    selections=Gui.Selection.getSelectionEx()
    names=[name for selection in selections for name in selection.SubElementNames]
    if len(names)>1:raise ValueError(tr('辺は1本だけ選択してください。','Select only one edge.'))
    if names and names[0].startswith('Edge'):
        if source.IndependentSheetKind not in core.ROOT_KINDS:raise ValueError(tr('連続曲げはフランジ全体を選択してください。','For a sequential bend, select the whole flange.'))
        return core.edge_from_selection(source,names[0])
    if names and names[0].startswith('Vertex'):raise ValueError(tr('ベース板または境界の辺を選択してください。','Select the base plate or a boundary edge.'))
    return '+X'

def show(ws,kind,existing=None,*,bend_mode=None):
    if kind=='PerforatedBase':return show_holes(ws,existing)
    if kind=='Tray':return show_tray(ws,existing)
    if Gui.Control.activeDialog():raise ValueError(tr('開いている編集を終了してください。','Finish the open task first.'))
    doc=ws.doc();source=None
    initial_edge='+X'
    sketch_center=None
    if kind=='Bend':
        objects=Gui.Selection.getSelection()
        sketches=[obj for obj in objects if obj.isDerivedFrom('Sketcher::SketchObject')]
        if existing is None and len(objects)==2 and len(sketches)==1:
            source=next(obj for obj in objects if obj!=sketches[0])
            initial_edge,sketch_center=core.bend_line_from_sketch(source,sketches[0])
        else:
            if bend_mode=='sketch':
                raise ValueError(tr('板と曲げ線のスケッチを同時に選択してください。',
                                    'Select a plate and bend-line sketch together.'))
            source=existing.Source if existing else selected(None)
        core.chain(source)
        if sketch_center is None and source.IndependentSheetKind in core.ROOT_KINDS:initial_edge=core.settings(existing).get('edge','+X') if existing else selected_base_edge(source)
    if kind=='Flat':
        obj=core.make(doc,'Flat',source=selected(None));Gui.Selection.clearSelection();Gui.Selection.addSelection(obj);ws.refresh();ws.fit();return obj
    values=core.settings(existing) if existing else (dict(length=80,width=40,thickness=1) if kind=='Base' else dict(radius=2,angle=90,height=25,k=.4))
    spec=[('length','長さ（接線まで）','Length to tangent',1,10000),('width','幅','Width',1,10000),('thickness','板厚','Thickness',.05,100)] if kind=='Base' else [('radius','内側曲げ半径','Inside bend radius',.05,10000),('angle','曲げ角度（±度）','Signed bend angle (deg)',-180,180),('height','フランジ直線長','Flange straight length',1,10000),('k','K係数','K factor',0,1)]
    if bend_mode=='hem':
        values['angle']=180
    if sketch_center is not None:
        values['center']=sketch_center
    if 'center' in values:
        spec=[field for field in spec if field[0]!='height']
        spec.append(('center','曲げ中心位置 (mm)','Bend center position (mm)',0,10000))
    dialog=W.QDialog(ws.main);dialog.setObjectName('IndependentSheetDialog');dialog.setWindowTitle(tr('独自板金・試作','Independent sheet prototype'))
    layout=W.QFormLayout(dialog)
    hint=W.QLabel(tr('末端へ最大8曲げを追加できます。角度の正負で曲げ方向を指定します。展開には材料・工具ごとのK係数校正が必要です。','Add up to 8 sequential bends at the terminal edge. Signed angles select direction. Calibrate K for the material/tooling.'));hint.setWordWrap(True);layout.addRow(hint)
    edge_choice=None
    if kind=='Bend' and source.IndependentSheetKind in core.ROOT_KINDS:
        edge_choice=W.QComboBox();edge_choice.setObjectName('IndependentSheetBaseEdge');edge_choice.addItems(list(core.BASE_EDGES));edge_choice.setCurrentText(initial_edge)
        edge_choice.setEnabled('center' not in values)
        layout.addRow(tr('最初に曲げるベース辺','First base edge'),edge_choice)
    fields={}
    for key,ja,en,lo,hi in spec:
        spin=W.QDoubleSpinBox();spin.setDecimals(6);spin.setRange(lo,hi);spin.setValue(values[key]);fields[key]=spin;layout.addRow(tr(ja,en),spin)
    if kind=='Bend':
        presets = W.QHBoxLayout()
        for angle, ja, en in ((180,'上向きヘム','Upward hem'),(-180,'下向きヘム','Downward hem')):
            button = W.QPushButton(tr(ja,en))
            button.clicked.connect(lambda checked=False, angle=angle: fields['angle'].setValue(angle))
            presets.addWidget(button)
        reverse = W.QPushButton(tr('曲げ方向を反転','Reverse bend direction'))
        reverse.clicked.connect(lambda: fields['angle'].setValue(-fields['angle'].value()))
        presets.addWidget(reverse)
        layout.addRow(presets)
    if kind=='Bend':
        calibrate = W.QPushButton(tr('実測の曲げ伸びからK係数を設定…','Set K from measured bend allowance…'))
        layout.addRow(calibrate)

        def calibrate_k():
            radius = fields['radius'].value()
            angle = math.radians(abs(fields['angle'].value()))
            thickness = core.source_dimensions(source)[2]
            if not angle:
                status.setText(tr('曲げ角度を指定してください。','Enter a bend angle.'))
                return
            low,high = angle*radius,angle*(radius+thickness)
            current = angle*(radius+fields['k'].value()*thickness)
            measured,accepted = W.QInputDialog.getDouble(
                dialog,tr('実測曲げ伸び','Measured bend allowance'),
                tr('曲げ伸び (mm)','Bend allowance (mm)'),current,0,100000,9)
            if accepted:
                if not low-1e-9 <= measured <= high+1e-9:
                    status.setText(tr('実測値から求めたK係数が0〜1の範囲外です。',
                                      'Measured allowance gives a K factor outside 0 to 1.'))
                    return
                fields['k'].setValue(max(0,min(1,(measured/angle-radius)/thickness)))
                status.clear()

        calibrate.clicked.connect(calibrate_k)
    jog = None
    if kind=='Bend' and existing is None and 'center' not in values:
        jog = W.QCheckBox(tr('逆方向の曲げを続けて段曲げを作成','Add reverse bend to create a jog'))
        return_length = W.QDoubleSpinBox()
        return_length.setDecimals(6)
        return_length.setRange(1,10000)
        return_length.setValue(25)
        return_length.setEnabled(False)
        jog.toggled.connect(return_length.setEnabled)
        layout.addRow(jog)
        layout.addRow(tr('段曲げ後の直線長 (mm)','Jog return length (mm)'),return_length)
    status=W.QLabel();status.setWordWrap(True);layout.addRow(status)
    buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addRow(buttons)
    def accept():
        try:
            parameters={key:spin.value() for key,spin in fields.items()}
            if edge_choice is not None:parameters['edge']=edge_choice.currentText()
            if jog is not None and jog.isChecked():
                result=core.make_jog(doc,source,return_length=return_length.value(),**parameters)
            else:
                result=core.make(doc,kind,source=source,existing=existing,**parameters)
            Gui.Selection.clearSelection();Gui.Selection.addSelection(result);ws.refresh();ws.fit();dialog.accept()
        except Exception as error:status.setText(str(error))
    buttons.accepted.connect(accept);buttons.rejected.connect(dialog.reject);dialog.resize(560,300);dialog.exec();dialog.deleteLater()

def export(ws):
    flat=selected('Flat')
    polylines = tr('閉じたポリライン付き DXF','DXF with closed polylines')+' (*.dxf)'
    cut_only = tr('切断輪郭のみ DXF','DXF cut contours only')+' (*.dxf)'
    path, file_filter = W.QFileDialog.getSaveFileName(
        ws.main, tr('展開DXFを保存','Save developed DXF'), 'Independent-sheet.dxf',
        'DXF (*.dxf);;'+polylines+';;'+cut_only)
    if path:
        core.export_dxf(flat,path,closed_polylines=file_filter in (polylines,cut_only),
                        include_bends=file_filter!=cut_only)


def show_tray(ws,existing=None):
    if Gui.Control.activeDialog():raise ValueError(tr('開いている編集を終了してください。','Finish the open task first.'))
    doc=ws.doc();source=existing.Source if existing else selected(None);core.owned(source)
    if source.IndependentSheetKind not in core.ROOT_KINDS:raise ValueError(tr('ベース板を選択してください。','Select a base panel.'))
    length,width,t=core.source_dimensions(source)
    values=core.settings(existing) if existing else dict(gap=min(2*t,min(length,width)/4),walls=core.default_walls())
    dialog=W.QDialog(ws.main);dialog.setObjectName('IndependentTrayDialog');dialog.setWindowTitle(tr('独自板金・複数側面','Independent sheet: multiple sides'))
    layout=W.QFormLayout(dialog)
    hint=W.QLabel(tr('ベース板の4辺へ個別に壁を作ります。端部の逃げ幅で隣接壁を離します。加工順序・工具干渉は検証しません。','Create independent walls on four base sides. End setbacks separate adjacent walls. Forming sequence and tooling clearance are not validated.'));hint.setWordWrap(True);layout.addRow(hint)
    gap=W.QDoubleSpinBox();gap.setObjectName('IndependentTrayGap');gap.setDecimals(6);gap.setRange(t,min(length,width)/2-t);gap.setValue(values['gap']);layout.addRow(tr('壁端部の後退量','Wall end setback'),gap)
    relief = W.QDoubleSpinBox()
    relief.setObjectName('IndependentTrayRelief')
    relief.setDecimals(4)
    relief.setRange(0,min(length,width)/2)
    relief.setValue(values.get('relief',0))
    relief.setSpecialValueText(tr('なし','None'))
    layout.addRow(tr('曲げ端の正方形逃げ (mm)','Square bend-end relief (mm)'),relief)
    table=W.QTableWidget(4,8);table.setObjectName('IndependentTrayWalls');table.setHorizontalHeaderLabels([tr('辺','Side'),tr('使用','Use'),tr('内側半径','Inside radius'),tr('角度±度','Angle ±deg'),tr('直線長','Straight length'),tr('K係数','K factor')]);table.horizontalHeader().setSectionResizeMode(W.QHeaderView.Stretch);table.setMinimumHeight(190)
    controls=[]
    for row,v in enumerate(values['walls']):
        table.setCellWidget(row,0,W.QLabel(v['edge']));enabled=W.QCheckBox();enabled.setChecked(v['enabled']);table.setCellWidget(row,1,enabled);fields={}
        for col,(key,lo,hi) in enumerate([('radius',.05,10000),('angle',-180,180),('height',1,10000),('k',0,1)],2):
            spin=W.QDoubleSpinBox();spin.setDecimals(6);spin.setRange(lo,hi);spin.setValue(v[key]);table.setCellWidget(row,col,spin);fields[key]=spin
        for column,key,label in ((6,'setback',tr('共通値','Common')),(7,'end_setback',tr('始点側と同じ','Same as start'))):
            setback = W.QDoubleSpinBox()
            setback.setDecimals(6)
            setback.setRange(0, length if v['edge'] in ('+Y','-Y') else width)
            setback.setSpecialValueText(label)
            setback.setValue(v.get(key,0))
            table.setCellWidget(row,column,setback)
            fields[key] = setback
        controls.append((v['edge'],enabled,fields))
    layout.addRow(table)
    directions = W.QHBoxLayout()
    for angle,ja,en in ((90,'全辺を上向き','All sides up'),(-90,'全辺を下向き','All sides down')):
        button = W.QPushButton(tr(ja,en))
        def set_angles(checked=False, angle=angle):
            for _,enabled,fields in controls:
                if enabled.isChecked():
                    fields['angle'].setValue(angle)
        button.clicked.connect(set_angles)
        directions.addWidget(button)
    layout.addRow(directions)
    status=W.QLabel();status.setObjectName('IndependentTrayStatus');status.setWordWrap(True);layout.addRow(status)
    buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addRow(buttons)
    def wall_values():
        return [dict(edge=edge,enabled=enabled.isChecked(),**{key:spin.value() for key,spin in fields.items()}) for edge,enabled,fields in controls]

    check = buttons.addButton(tr('壁とコーナーを検査','Check walls and corners'),W.QDialogButtonBox.ActionRole)
    def check_tray():
        try:
            clearances = []
            core.tray_shape(length,width,t,gap.value(),wall_values(),
                            holes=core.holes_of(source),clearances=clearances,relief=relief.value())
            message = tr('壁とコーナーの形状検査に合格しました。','Wall and corner geometry passed.')
            if clearances:
                distance,first,second = min(clearances)
                message += ' ' + tr('壁間の最小距離 {}–{} は {:.6g} mm。','Minimum wall gap {}–{} is {:.6g} mm.').format(first,second,distance)
                measurements = [
                    tr('{} と {}  {:.6g} mm','{} and {}  {:.6g} mm').format(first,second,distance)
                    for distance,first,second in sorted(clearances)
                ]
                message += '\n' + '\n'.join(measurements)
            status.setText(message)
        except Exception as exc:
            status.setText(str(exc))
    check.clicked.connect(check_tray)

    def accept():
        try:
            walls=wall_values()
            obj=core.make(doc,'Tray',source=source,existing=existing,gap=gap.value(),walls=walls,relief=relief.value())
            Gui.Selection.clearSelection();Gui.Selection.addSelection(obj);ws.refresh();ws.fit();dialog.accept()
        except Exception as exc:status.setText(str(exc))
    buttons.accepted.connect(accept);buttons.rejected.connect(dialog.reject);dialog.resize(900,390);dialog.exec();dialog.deleteLater()

def export_table(ws):
    obj=selected(None)
    path,_=W.QFileDialog.getSaveFileName(ws.main,tr('曲げ表CSVを保存','Save bend table CSV'),'Independent-bend-table.csv','CSV (*.csv)')
    if path:core.export_bend_table(obj,path)


def show_holes(ws,existing=None):
    if Gui.Control.activeDialog():raise ValueError(tr('開いている編集を終了してください。','Finish the open task first.'))
    doc=ws.doc()
    if existing is None:
        chosen=selected(None);root=core.panel_root(chosen)
        if root.IndependentSheetKind=='PerforatedBase':existing=root
        else:
            candidates=[child for child in root.InList if isinstance(getattr(child,'Proxy',None),core.Feature) and child.IndependentSheetKind=='PerforatedBase' and child.Source==root]
            if len(candidates)>1:raise ValueError(tr('編集する穴付きベースか、その曲げ結果を選択してください。','Select the perforated base or formed result to edit.'))
            if candidates:existing=candidates[0]
        source=existing.Source if existing else root
    else:source=existing.Source
    core.owned(source,'Base');length,width,t=core.source_dimensions(source)
    if existing:holes=core.settings(existing)['holes']
    else:
        radius=max(.05,min(2,min(length,width)/12));margin=max(t+radius,min(length,width)*.2)
        holes=[dict(x=x,y=y,radius=radius) for x,y in ((margin,margin),(length-margin,margin),(length-margin,width-margin),(margin,width-margin))]
        try:core.hole_values(length,width,t,holes)
        except ValueError:holes=[dict(x=length/2,y=width/2,radius=radius)]
    dialog=W.QDialog(ws.main);dialog.setObjectName('IndependentHolesDialog');dialog.setWindowTitle(tr('独自板金・ベース穴','Independent sheet: base holes'))
    layout=W.QVBoxLayout(dialog);hint=W.QLabel(tr('ベース板のローカルXYで丸穴と長穴を指定します。直線部0は丸穴です。長穴の全長は直線部＋直径です。矩形幅と高さを両方指定すると矩形開口になります。板端・穴同士に板厚以上を残します。既存の曲げ・トレイは一括で穴付きベースへ接続します。','Round holes and slots in base-local XY. Zero straight length makes a circle. Overall slot length is straight length plus diameter. Set both rectangle dimensions for a rectangular opening. Leave at least one thickness to edges and between holes. Existing bends/trays are linked atomically.'));hint.setWordWrap(True);layout.addWidget(hint)
    table=W.QTableWidget(0,8);table.setObjectName('IndependentHolesTable');table.setHorizontalHeaderLabels(['X (mm)','Y (mm)',tr('半径 (mm)','Radius (mm)'),tr('直線部 (mm)','Straight length (mm)'),tr('方向','Axis'),tr('矩形幅 (mm)','Rect. width (mm)'),tr('矩形高さ (mm)','Rect. height (mm)'),tr('多角形の頂点','Polygon vertices')]);table.horizontalHeader().setSectionResizeMode(W.QHeaderView.Stretch);layout.addWidget(table)
    def add(hole=None):
        if table.rowCount()>=core.MAX_HOLES:return
        hole=hole or dict(x=length/2,y=width/2,radius=max(.05,min(2,min(length,width)/12)))
        row=table.rowCount();table.insertRow(row)
        for col,(key,hi) in enumerate([('x',length),('y',width),('radius',min(length,width)/2),('span',max(length,width))]):
            spin=W.QDoubleSpinBox();spin.setDecimals(6);spin.setRange(.05 if key=='radius' else 0,hi);spin.setValue(hole.get(key,0));table.setCellWidget(row,col,spin)
        axis=W.QComboBox();axis.addItems(['X','Y']);axis.setCurrentIndex(int(hole.get('vertical',False)));table.setCellWidget(row,4,axis)
        for col, key, limit in ((5, 'rect_width', length), (6, 'rect_height', width)):
            spin = W.QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(0, limit)
            spin.setValue(hole.get(key, 0))
            table.setCellWidget(row, col, spin)
        vertices = {'profile': hole['profile']} if hole.get('profile') else hole.get('polygon')
        cell = W.QLineEdit()
        cell.setMaxLength(262144)
        if vertices:
            cell.setText(json.dumps(vertices, separators=(',', ':')))
        cell.setToolTip('[[dx,dy],[dx,dy],[dx,dy]] (mm)')
        table.setCellWidget(row, 7, cell)
    for hole in holes:add(hole)
    row=W.QHBoxLayout();plus=W.QPushButton(tr('穴を追加','Add hole'));plus.setObjectName('IndependentHoleAdd');minus=W.QPushButton(tr('選択行を削除','Remove selected row'));row.addWidget(plus);row.addWidget(minus);layout.addLayout(row)
    table.setSelectionBehavior(W.QAbstractItemView.SelectRows)
    table.setSelectionMode(W.QAbstractItemView.ExtendedSelection)
    count_label = W.QLabel()
    count_label.setObjectName('IndependentHoleCount')
    row.addWidget(count_label)

    def update_count(*_):
        count_label.setText(tr('開口 {}/{}','Cutouts {}/{}').format(table.rowCount(),core.MAX_HOLES))
        plus.setEnabled(table.rowCount()<core.MAX_HOLES)

    table.model().rowsInserted.connect(update_count)
    table.model().rowsRemoved.connect(update_count)
    update_count()
    minus.setText(tr('選択行をまとめて削除','Remove selected rows'))

    def selected_rows():
        return sorted(index.row() for index in table.selectionModel().selectedRows())

    def remove_selected():
        rows = selected_rows()
        if not rows and table.rowCount():
            rows.append(table.currentRow() if table.currentRow() >= 0 else table.rowCount()-1)
        for index in sorted(rows, reverse=True):
            table.removeRow(index)

    plus.clicked.connect(lambda:add())
    minus.clicked.connect(remove_selected)
    status=W.QLabel();status.setObjectName('IndependentHolesStatus');status.setWordWrap(True);layout.addWidget(status);buttons=W.QDialogButtonBox(W.QDialogButtonBox.Ok|W.QDialogButtonBox.Cancel);layout.addWidget(buttons)
    from_sketch = W.QPushButton(tr('スケッチから開口を追加…','Add cutout from sketch…'))
    from_sketch.setObjectName('IndependentHoleFromSketch')
    row.addWidget(from_sketch)
    row.addWidget(W.QLabel(tr('曲線の分割設定 (mm)','Curve subdivision (mm)')))
    deflection = W.QDoubleSpinBox()
    deflection.setDecimals(3)
    deflection.setRange(.001, .05)
    deflection.setSingleStep(.001)
    deflection.setValue(.005)
    deflection.setToolTip(tr('値が小さいほど分割が細かくなります。楕円・楕円弧・Bスプラインの取り込み時に適用します。',
                             'Smaller values increase subdivision when importing ellipses, elliptical arcs and B-splines.'))
    row.addWidget(deflection)

    check_sketch = W.QPushButton(tr('スケッチを検査…','Check cutout sketch…'))
    check_sketch.setObjectName('IndependentHoleCheckSketch')
    row.addWidget(check_sketch)

    edit_row = W.QHBoxLayout()
    layout.insertLayout(2, edit_row)
    offsets = []
    for caption, limit in (('ΔX (mm)', length), ('ΔY (mm)', width)):
        edit_row.addWidget(W.QLabel(caption))
        field = W.QDoubleSpinBox()
        field.setDecimals(6)
        field.setRange(-limit, limit)
        edit_row.addWidget(field)
        offsets.append(field)
    duplicate = W.QPushButton(tr('選択行を複製','Duplicate selected rows'))
    duplicate.setObjectName('IndependentHoleDuplicate')
    edit_row.addWidget(duplicate)

    move = W.QPushButton(tr('選択行を移動','Move selected rows'))
    move.setObjectName('IndependentHoleMove')
    edit_row.addWidget(move)

    def translate_rows(copy_rows):
        rows = selected_rows()
        if not rows:
            status.setText(tr('開口の行を選択してください。','Select one or more cutout rows.'))
            return
        try:
            values = table_values()
            dx, dy = [field.value() for field in offsets]
            translated = [dict(values[i], x=values[i]['x']+dx, y=values[i]['y']+dy) for i in rows]
            if copy_rows:
                core.hole_values(length, width, t, values+translated)
                for copy in translated:
                    add(copy)
            else:
                for index, value in zip(rows, translated):
                    values[index] = value
                core.hole_values(length, width, t, values)
                for index, value in zip(rows, translated):
                    table.cellWidget(index,0).setValue(value['x'])
                    table.cellWidget(index,1).setValue(value['y'])
            status.clear()
        except Exception as exc:
            status.setText(str(exc))

    duplicate.clicked.connect(lambda: translate_rows(True))
    move.clicked.connect(lambda: translate_rows(False))

    def import_sketch(check_only=False):
        if table.rowCount() >= core.MAX_HOLES:
            status.setText(tr('開口は最大32個です。','At most 32 cutouts are supported.'))
            return
        sketches = [obj for obj in doc.Objects if obj.isDerivedFrom('Sketcher::SketchObject')]
        if not sketches:
            status.setText(tr('文書にスケッチがありません。','There are no sketches in this document.'))
            return
        names = [f'{obj.Label} ({obj.Name})' for obj in sketches]
        name, accepted = W.QInputDialog.getItem(dialog, tr('開口スケッチ','Cutout sketch'),
                                                tr('閉じた輪郭を含むスケッチ（楕円・Bスプラインは直線近似）','Sketch with closed outlines (ellipses and B-splines are approximated by lines)'),
                                                names, 0, False)
        if accepted:
            try:
                cutouts = core.cutouts_from_sketch(source, sketches[names.index(name)],
                                                   deflection=deflection.value())
                core.hole_values(length, width, t, table_values()+cutouts)
                if check_only:
                    status.setText(tr('{} 個の開口を追加できます。','{} cutouts can be added.').format(len(cutouts)))
                    return
                for cutout in cutouts:
                    add(cutout)
                status.clear()
            except Exception as exc:
                status.setText(str(exc))

    from_sketch.clicked.connect(lambda: import_sketch())
    check_sketch.clicked.connect(lambda: import_sketch(check_only=True))

    def table_values():
        values=[dict(zip(('x','y','radius','span'),[table.cellWidget(row,col).value() for col in range(4)]),vertical=bool(table.cellWidget(row,4).currentIndex()),rect_width=table.cellWidget(row,5).value(),rect_height=table.cellWidget(row,6).value()) for row in range(table.rowCount())]
        for row, value in enumerate(values):
            vertices = table.cellWidget(row, 7).text().strip()
            if vertices:
                outline = json.loads(vertices)
                if isinstance(outline, dict) and set(outline) == {'profile'} and outline['profile']:
                    value['profile'] = outline['profile']
                    continue
                value['polygon'] = outline
                if not value['polygon']:
                    raise ValueError(tr('多角形には3点以上を入力してください。','Enter at least three polygon vertices.'))
        return values

    def accept():
        try:
            values = table_values()
            obj=core.make(doc,'PerforatedBase',source=source,existing=existing,holes=values)
            visible=[child for child in obj.InListRecursive if hasattr(child,'ViewObject') and child.Visibility]
            selected_result=visible[-1] if visible else obj
            Gui.Selection.clearSelection();Gui.Selection.addSelection(selected_result);ws.refresh();ws.fit();dialog.accept()
        except Exception as exc:status.setText(str(exc))
    buttons.accepted.connect(accept);buttons.rejected.connect(dialog.reject);dialog.resize(1000,430);dialog.exec();dialog.deleteLater()


def unfold_sketch(ws):
    sketch = core.make_flat_sketch(selected('Flat'))
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(sketch)
    ws.refresh()
    ws.fit()


def refresh_flats(ws):
    count, errors = core.refresh_flats(ws.doc())
    ws.refresh()
    message = tr('更新した展開: ', 'Updated developments: ') + str(count)
    if errors:
        W.QMessageBox.warning(ws.main, tr('独自展開', 'Independent development'), message + '\n' + tr('更新できなかった展開: ', 'Failed developments: ') + ', '.join(errors))
    else:
        App.Console.PrintMessage(message + '\n')
