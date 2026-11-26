"""Fusion-inspired command ribbon, using original icons and FreeCAD commands."""
from i18n import tr
import os
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets as W

STYLE = '''
QToolBar#FluxCADToolbar {background:#f5f5f5;border:0;border-bottom:1px solid #d6d6d6;padding:0;spacing:0;}
QWidget#FluxRibbon {background:#f5f5f5;color:#333;font-family:"Yu Gothic UI";font-size:12px;}
QFrame#FluxTop {background:#e9e9e9;border-bottom:1px solid #d6d6d6;}
QToolButton {padding:1px 4px;border:1px solid transparent;border-radius:2px;}
QWidget#FluxRibbon QToolButton:hover {background:#dcebf7;border:1px solid #9bc4e5;}
QWidget#FluxRibbon QToolButton:pressed {background:#c4e0f5;}
QTabBar::tab {background:transparent;padding:3px 15px;color:#555;border:0;border-bottom:2px solid transparent;}
QTabBar::tab:selected {color:#303030;border-bottom:2px solid #444;font-weight:bold;}
QTabBar::tab:disabled {color:#a6aaae;}
QFrame#FluxGroup {border-right:1px solid #d3d3d3;}
QToolButton#FluxGroupLabel {padding:0px 8px;font-size:11px;color:#4c5259;}
QToolButton#FluxWorkspace {border:1px solid #c4c4c4;border-radius:4px;background:#f9f9f9;font-size:13px;}
QLabel#FluxDocTitle {color:#636971;font-size:12px;}
QMenu {background:#fff;color:#303740;border:1px solid #c1c7ce;padding:5px;}
QMenu::item {padding:6px 30px 6px 12px;}
QMenu::item:selected {background:#dcebf7;}
QMenu::separator {height:1px;background:#e2e5e7;margin:4px 10px;}
'''


def build(ws):
    root = W.QWidget()
    root.setObjectName('FluxRibbon')
    layout = W.QVBoxLayout(root)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(0)
    ws.ribbon = root
    ws.ribbon_actions = {}
    ws.ribbon_menus = {}
    ws.solid_action_keys = ['extrude','revolve','loft','sweep','box','cylinder','hole','fillet','chamfer','shell','move','move_numeric','move_copy','align','join','cut','split_body','linear_pattern','circular_pattern','mirror','offset_plane','rectangle','mesh_scale','mesh_rotate','mesh_translate']

    def action(key, text, icon, callback, shortcut=None):
        path = os.path.join(os.path.dirname(__file__),'icons',icon+'.svg')
        ico = QtGui.QIcon(path if os.path.exists(path) else ':/icons/'+icon+'.svg')
        a = QtGui.QAction(ico,text,root)
        a.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False: ws.safe(callback),(1, 0, False, False)))
        a.setToolTip(text + ('  ['+shortcut+']' if shortcut else ''))
        ws.actions.append((a,shortcut,callback))
        ws.ribbon_actions[key] = a
        return a

    def command(name):
        return __import__('builtins')._fullarc_qt_slot(lambda: Gui.runCommand(name),(0, 0, False, False))

    action('new',tr('新規デザイン'),'document-new',command('Std_New'))
    action('open',tr('開く…'),'document-open',command('Std_Open'))
    import cam_post_ui
    import cam_sim_ui
    import cam_face_ui
    import cam_drill_ui
    import cam_pocket_ui
    action('cam_post',tr('Gコード出力…','Post Process / G-code…'),'Path-Post',__import__('builtins')._fullarc_qt_slot(lambda:cam_post_ui.show(ws),(0, 0, False, False)))
    action('cam_sim',tr('加工シミュレーション…','Machining Simulation…'),'CAM_Simulator',__import__('builtins')._fullarc_qt_slot(lambda:cam_sim_ui.show(ws),(0, 0, False, False)))
    action('cam_face',tr('面加工…','Facing…'),'Path-MillFace',__import__('builtins')._fullarc_qt_slot(lambda:cam_face_ui.show(ws),(0, 0, False, False)))
    action('cam_drill',tr('穴あけ加工…','Drilling…'),'Path-Drilling',__import__('builtins')._fullarc_qt_slot(lambda:cam_drill_ui.show(ws),(0, 0, False, False)))
    action('cam_pocket',tr('2Dポケット加工…','2D Pocket…'),'Path-Pocket',__import__('builtins')._fullarc_qt_slot(lambda:cam_pocket_ui.show(ws),(0, 0, False, False)))
    import cam_profile_ui
    action('cam_profile',tr('2D輪郭加工…','2D Contour…'),'Path-Profile',__import__('builtins')._fullarc_qt_slot(lambda:cam_profile_ui.show(ws),(0, 0, False, False)))
    import cam_setup_ui
    action('cam_setup',tr('加工セットアップ…','Machining Setup…'),'preferences-system',__import__('builtins')._fullarc_qt_slot(lambda:cam_setup_ui.show(ws),(0, 0, False, False)))
    import bom_ui
    action('bom',tr('部品表を作成…','Create Bill of Materials…'),'spreadsheet',__import__('builtins')._fullarc_qt_slot(lambda:bom_ui.show(ws),(0, 0, False, False)))
    import solidworks_import
    solidworks_import.register()
    action('solidworks_open',tr('SolidWorksを読み込み…','Import SolidWorks…'),'document-open',__import__('builtins')._fullarc_qt_slot(lambda:solidworks_import.show(ws),(0, 0, False, False)))
    import solidworks_brep
    action('solidworks_brep_open',tr('SolidWorks厳密ソリッドを読み込み…','Import SolidWorks Native Solids…'),'document-open',__import__('builtins')._fullarc_qt_slot(lambda:solidworks_brep.show(ws),(0, 0, False, False)))
    action('save',tr('保存'),'document-save',__import__('builtins')._fullarc_qt_slot(lambda:__import__('save_guard').save(ws),(0, 0, False, False)))
    add_save_as(action, command, ws)
    import example_tools
    action('examples',tr('使用例を作業コピーで開く…','Open Example Working Copy…'),'document-open',__import__('builtins')._fullarc_qt_slot(lambda:example_tools.show(ws),(0, 0, False, False)))
    import example_guide
    action('example_guide',tr('使用例のガイド…','Example Guide…'),'document-open',__import__('builtins')._fullarc_qt_slot(lambda:example_guide.show(ws),(0, 0, False, False)))
    action('undo',tr('元に戻す'),'edit-undo',command('Std_Undo'))
    action('redo',tr('やり直す'),'edit-redo',command('Std_Redo'))
    import drawing, drawing_detail, parameter_panel
    import balloon_ui
    import leader_ui
    import weld_ui
    action('drawing_weld',tr('溶接記号…','Welding Symbol…'),'drawing-note',__import__('builtins')._fullarc_qt_slot(lambda:weld_ui.show(ws),(0, 0, False, False)))
    action('drawing_leader',tr('引出線付き注記…','Leader Note…'),'drawing-note',__import__('builtins')._fullarc_qt_slot(lambda:leader_ui.show(ws),(0, 0, False, False)))
    action('drawing_balloon',tr('部品番号バルーン…','Item Balloon…'),'drawing-note',__import__('builtins')._fullarc_qt_slot(lambda:balloon_ui.show(ws),(0, 0, False, False)))
    action('parameters',tr('パラメータを変更','Change Parameters'),'parameters',__import__('builtins')._fullarc_qt_slot(lambda:parameter_panel.show(ws),(0, 0, False, False)))
    import alternating_polygon
    action('alternating_polygon',tr('2種類の辺の多角形…','Alternating Side Polygon…'),'polygon',__import__('builtins')._fullarc_qt_slot(lambda:alternating_polygon.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('alternating_polygon')
    for key,ja,en,icon,callback in [
        ('drawing_new','新規図面','New Drawing','drawing-page',__import__('builtins')._fullarc_qt_slot(lambda:drawing.new_page(ws),(0, 0, False, False))),
        ('drawing_open','図面を開く','Open Drawing','drawing-page',__import__('builtins')._fullarc_qt_slot(lambda:drawing.open_page(ws),(0, 0, False, False))),
        ('drawing_sheet','用紙設定','Sheet Settings','drawing-page',__import__('builtins')._fullarc_qt_slot(lambda:drawing.sheet_settings(ws),(0, 0, False, False))),
        ('drawing_view','ベースビュー','Base View','drawing-view',__import__('builtins')._fullarc_qt_slot(lambda:drawing.insert_view(ws),(0, 0, False, False))),
        ('drawing_projection','三面図','Projected Views','drawing-projection',__import__('builtins')._fullarc_qt_slot(lambda:drawing.insert_view(ws,group=True),(0, 0, False, False))),
        ('drawing_edit','選択項目を編集','Edit Selection','drawing-view',__import__('builtins')._fullarc_qt_slot(lambda:drawing.edit_selected(ws),(0, 0, False, False))),
        ('drawing_note','注記','Note','drawing-note',__import__('builtins')._fullarc_qt_slot(lambda:drawing.annotation(ws),(0, 0, False, False))),
        ('drawing_frames','図の枠を表示 / 非表示','Toggle View Frames','drawing-view',__import__('builtins')._fullarc_qt_slot(lambda:drawing.toggle_frames(ws),(0, 0, False, False))),
        ('drawing_display','図の配置と表示','View Placement and Display','drawing-view',__import__('builtins')._fullarc_qt_slot(lambda:drawing_detail.view_settings(ws),(0, 0, False, False))),
        ('drawing_pdf','PDF出力…','Export PDF…','drawing-export',__import__('builtins')._fullarc_qt_slot(lambda:drawing.export_page(ws,'pdf'),(0, 0, False, False))),
        ('drawing_svg','SVG出力…','Export SVG…','drawing-export',__import__('builtins')._fullarc_qt_slot(lambda:drawing.export_page(ws,'svg'),(0, 0, False, False))),
        ('drawing_design','デザインに戻る','Return to Design','Part_Box',__import__('builtins')._fullarc_qt_slot(lambda:drawing.switch(ws,False),(0, 0, False, False)))]:
        action(key,tr(ja,en),icon,callback);ws.solid_action_keys.append(key)
    for key,ja,en in [('length','長さ寸法','Length Dimension'),('horizontal','水平寸法','Horizontal Dimension'),
                      ('vertical','垂直寸法','Vertical Dimension'),('radius','半径寸法','Radius Dimension'),
                      ('diameter','直径寸法','Diameter Dimension'),('angle','角度寸法','Angle Dimension')]:
        action('drawing_'+key,tr(ja,en),'drawing-dimension',__import__('builtins')._fullarc_qt_slot(lambda k=key:drawing.dimension(ws,k),(1, 0, False, False)))
        ws.solid_action_keys.append('drawing_'+key)
    for key,ja,en,icon,tipja,tipen in [
        ('section','断面図','Section View','drawing-section','元の投影図を選び、切断方向と位置を設定します。','Select a base view, then set the cut direction and position.'),
        ('detail','詳細図','Detail View','drawing-detail','元の投影図を選び、拡大する範囲と倍率を設定します。','Select a base view, then set the detail region and magnification.'),
        ('hatch','ハッチング','Hatch','drawing-hatch','図面の面を選び、パターン・尺度・角度を設定します。','Select drawing faces and set the pattern, scale and angle.'),
        ('circle_center','中心マーク','Center Marks','drawing-center','図面の円・円弧を選び、中心線を追加します。','Select drawing circles or arcs to add centerlines.'),
        ('edge_center','2辺間の中心線','Centerline Between Edges','drawing-center','同じ投影図の2辺をCtrlで選択します。','Ctrl-select two edges in the same drawing view.'),
        ('face_center','面の中心線','Face Centerline','drawing-center','図面の面内部を選び、中心線を配置します。','Select drawing faces to position a centerline.'),
        ('erase','補助線を削除','Remove Cosmetic Geometry','drawing-center','図面の中心線・補助線を選択して削除します。','Select cosmetic edges or centerlines in the drawing to remove them.')]:
        a=action('drawing_'+key,tr(ja,en),icon,__import__('builtins')._fullarc_qt_slot(lambda k=key:drawing_detail.start(ws,k),(1, 0, False, False)))
        a.setToolTip(tr(tipja,tipen));ws.solid_action_keys.append('drawing_'+key)
    action('sketch',tr('スケッチを作成'),'Sketcher_NewSketch',ws.sketch)
    ws.ribbon_actions['sketch'].setToolTip(tr('選択した平面上に作成。面を選択していない場合は、表示グリッドの面に作成します。',
                                             'Create on the selected planar face, or on the displayed grid if no face is selected.'))
    action('sketch_plane',tr('平面を指定してスケッチ…','Sketch on Chosen Plane…'),'Sketcher_NewSketch',__import__('builtins')._fullarc_qt_slot(lambda:ws.sketch(choose_plane=True),(0, 0, False, False)))
    ws.solid_action_keys.append('sketch_plane')
    action('rectangle',tr('長方形スケッチ'),'Sketcher_CreateRectangle',ws.rectangle)
    action('extrude',tr('押し出し'),'extrude',ws.extrude,'E')
    action('revolve',tr('回転'),'revolve',ws.revolve)
    action('loft',tr('ロフト'),'loft',__import__('builtins')._fullarc_qt_slot(lambda:ws.section_feature('loft'),(0, 0, False, False)))
    action('sweep',tr('スイープ'),'sweep',__import__('builtins')._fullarc_qt_slot(lambda:ws.section_feature('sweep'),(0, 0, False, False)))
    import guided_sweep_ui
    action('guided_sweep',tr('ガイドレール付きスイープ…','Sweep with Guide Rail…'),'sweep',__import__('builtins')._fullarc_qt_slot(lambda:guided_sweep_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('guided_sweep')
    import four_ops_ui
    action('fixed_sweep',tr('断面姿勢固定スイープ…','Fixed Orientation Sweep…'),'sweep',__import__('builtins')._fullarc_qt_slot(lambda:four_ops_ui.show(ws,'fixed'),(0, 0, False, False)))
    ws.solid_action_keys.append('fixed_sweep')
    action('linear_pattern',tr('矩形状パターン','Rectangular Pattern'),'linear-pattern',__import__('builtins')._fullarc_qt_slot(lambda:ws.pattern('linear'),(0, 0, False, False)))
    action('circular_pattern',tr('円形状パターン'),'circular-pattern',__import__('builtins')._fullarc_qt_slot(lambda:ws.pattern('circular'),(0, 0, False, False)))
    action('path_pattern',tr('パスに沿ったパターン','Pattern on Path'),'path-pattern',__import__('builtins')._fullarc_qt_slot(lambda:ws.path_pattern_panel.start(),(0, 0, False, False)))
    ws.solid_action_keys.append('path_pattern')
    action('mirror',tr('ミラー'),'mirror',ws.mirror)
    action('box',tr('直方体'),'Part_Box',ws.box)
    action('cylinder',tr('円柱'),'Part_Cylinder',ws.cylinder)
    for key,label,en in [('sphere','球','Sphere'),('torus','トーラス','Torus'),('coil','コイル','Coil'),('spiral','平面スパイラル','Planar Spiral'),('pipe','パイプ','Pipe')]:
        action(key,tr(label,en),'coil' if key=='spiral' else key,__import__('builtins')._fullarc_qt_slot(lambda kind=key:ws.primitive_panel.start(kind),(1, 0, False, False)))
        ws.solid_action_keys.append(key)
    action('dome',tr('ドーム…','Dome…'),'sphere',__import__('builtins')._fullarc_qt_slot(lambda:ws.primitive_panel.start('dome'),(0, 0, False, False)))
    ws.solid_action_keys.append('dome')
    action('hole',tr('穴'),'hole',ws.hole,'H')
    action('fillet',tr('フィレット'),'Part_Fillet',ws.fillet,'F')
    action('chamfer',tr('面取り'),'chamfer',ws.chamfer)
    action('split_body',tr('ボディを分割','Split Body'),'split-body',ws.split_body)
    action('shell',tr('シェル（中空化）'),'shell',ws.shell)
    action('face_offset',tr('面をオフセット…','Offset Face…'),'shell',__import__('builtins')._fullarc_qt_slot(lambda:ws.face_offset.start(),(0, 0, False, False)))
    ws.solid_action_keys.append('face_offset')
    import defeature_ui
    action('delete_faces',tr('面を削除して埋める…','Delete Faces and Heal…'),'Part_Defeaturing',__import__('builtins')._fullarc_qt_slot(lambda:defeature_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('delete_faces')
    import solid_draft_ui
    action('solid_draft',tr('抜き勾配…','Solid Face Draft…'),'PartDesign_Draft',__import__('builtins')._fullarc_qt_slot(lambda:solid_draft_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('solid_draft')
    import angle_chamfer_ui
    action('angle_chamfer',tr('距離と角度の面取り…','Distance and Angle Chamfer…'),'PartDesign_Chamfer',__import__('builtins')._fullarc_qt_slot(lambda:angle_chamfer_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('angle_chamfer')
    action('offset_plane',tr('オフセット平面'),'offset-plane',ws.offset_plane)
    action('midplane',tr('中間平面','Midplane'),'midplane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('midplane'),(0, 0, False, False)))
    action('angled_plane',tr('角度付き平面','Plane at Angle'),'angled-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('angle'),(0, 0, False, False)))
    action('three_point_plane',tr('3点を通る平面','Plane Through Three Points'),'three-point-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('three_points'),(0, 0, False, False)))
    action('tangent_plane',tr('接平面','Tangent Plane'),'tangent-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('tangent'),(0, 0, False, False)))
    action('path_plane',tr('パスに沿った平面','Plane Along Path'),'path-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('along_path'),(0, 0, False, False)))
    ws.solid_action_keys.extend(['midplane','angled_plane','three_point_plane','tangent_plane','path_plane'])
    action('two_edge_plane',tr('2辺を通る平面','Plane Through Two Edges'),'three-point-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('two_edges'),(0, 0, False, False)))
    ws.solid_action_keys.append('two_edge_plane')
    action('tangent_point_plane',tr('面上の頂点での接平面','Tangent Plane at Vertex on Face'),'tangent-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('tangent_point'),(0, 0, False, False)))
    ws.solid_action_keys.append('tangent_point_plane')
    action('perpendicular_point_plane',tr('頂点を通る垂直平面','Perpendicular Plane Through Vertex'),'angled-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('perpendicular_point'),(0, 0, False, False)))
    ws.solid_action_keys.append('perpendicular_point_plane')
    action('offset_point_plane',tr('頂点を通る平行平面','Offset Plane Through Vertex'),'offset-plane',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_panel.start('offset_point'),(0, 0, False, False)))
    ws.solid_action_keys.append('offset_point_plane')
    import coordinate_plane_ui
    action('coordinate_plane',tr('座標と法線で平面…','Plane by Coordinates and Normal…'),'offset-plane',__import__('builtins')._fullarc_qt_slot(lambda:coordinate_plane_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('coordinate_plane')
    import coordinate_axis_ui
    action('coordinate_axis',tr('座標と方向で構築軸…','Construction Axis by Coordinates…'),'construction-axis',__import__('builtins')._fullarc_qt_slot(lambda:coordinate_axis_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('coordinate_axis')
    import coordinate_point_ui
    action('coordinate_point',tr('座標で構築点…','Construction Point by Coordinates…'),'vertex-point',__import__('builtins')._fullarc_qt_slot(lambda:coordinate_point_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('coordinate_point')
    import vertex_point_ui
    import three_plane_ui
    action('three_plane_point',tr('3平面を通る構築点…','Point Through Three Planes…'),'vertex-point',__import__('builtins')._fullarc_qt_slot(lambda:three_plane_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('three_plane_point')
    import edge_plane_ui
    action('edge_plane_point',tr('辺と平面の交点に構築点…','Point At Edge And Plane…'),'vertex-point',__import__('builtins')._fullarc_qt_slot(lambda:edge_plane_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('edge_plane_point')
    import edge_intersection_ui
    action('edge_intersection_point',tr('2辺を通る構築点…','Point Through Two Edges…'),'vertex-point',__import__('builtins')._fullarc_qt_slot(lambda:edge_intersection_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('edge_intersection_point')
    action('vertex_point',tr('頂点に構築点…','Point at Vertex…'),'PartDesign_Point',__import__('builtins')._fullarc_qt_slot(lambda:vertex_point_ui.show(ws),(0, 0, False, False)))
    import center_point_ui
    action('analytic_center_point',tr('円・球・トーラスの中心点…','Circle / Sphere / Torus Center Point…'),'point',__import__('builtins')._fullarc_qt_slot(lambda:center_point_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('analytic_center_point')
    import point_path_ui
    action('point_along_edge',tr('エッジに沿った構築点…','Point Along Edge…'),'point',__import__('builtins')._fullarc_qt_slot(lambda:point_path_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('point_along_edge')
    action('center_axis',tr('円柱・円すい・トーラスの中心軸','Axis Through Cylinder / Cone / Torus'),'center-axis',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_axis_panel.start('center'),(0, 0, False, False)))
    action('two_point_axis',tr('2点を通る軸','Axis Through Two Points'),'construction-axis',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_axis_panel.start('two_points'),(0, 0, False, False)))
    action('two_plane_axis',tr('2平面を通る軸','Axis Through Two Planes'),'construction-axis',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_axis_panel.start('two_planes'),(0, 0, False, False)))
    ws.solid_action_keys.extend(['center_axis','two_point_axis'])
    ws.solid_action_keys.append('two_plane_axis')
    action('normal_point_axis',tr('面上の頂点を通る法線軸','Normal Axis at Vertex on Face'),'construction-axis',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_axis_panel.start('normal_point'),(0, 0, False, False)))
    ws.solid_action_keys.append('normal_point_axis')
    action('edge_axis',tr('直線辺を通る軸','Axis Through Straight Edge'),'construction-axis',__import__('builtins')._fullarc_qt_slot(lambda:ws.construction_axis_panel.start('edge'),(0, 0, False, False)))
    ws.solid_action_keys.append('edge_axis')
    action('move',tr('移動（ドラッグ）'),'move',ws.start_move,'M').setCheckable(True)
    action('move_numeric',tr('数値で移動…'),'move',ws.move)
    action('move_copy',tr('移動 / コピー（回転）…'),'body-rotate',ws.move_copy)
    action('mesh_scale',tr('メッシュのサイズ変更…','Resize Mesh…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:ws.edit_mesh('scale'),(0, 0, False, False)))
    action('mesh_rotate',tr('メッシュの回転…','Rotate Mesh…'),'body-rotate',__import__('builtins')._fullarc_qt_slot(lambda:ws.edit_mesh('rotate'),(0, 0, False, False)))
    action('mesh_translate',tr('メッシュの移動…','Move Mesh…'),'move',__import__('builtins')._fullarc_qt_slot(lambda:ws.edit_mesh('translate'),(0, 0, False, False)))
    import tessellate_ui
    action('mesh_tessellate',tr('CAD形状からメッシュを作成…','Create Mesh from CAD…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:tessellate_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_tessellate')
    import mesh_section_ui
    action('mesh_section',tr('メッシュ断面スケッチ…','Mesh Section Sketch…'),'sketch-create',__import__('builtins')._fullarc_qt_slot(lambda:mesh_section_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_section')
    import mesh_convert_ui
    action('mesh_convert',tr('メッシュをCAD形状へ変換…','Convert Mesh to CAD…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:mesh_convert_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_convert')
    import mesh_merge_ui
    action('mesh_merge',tr('メッシュを統合…','Merge Meshes…'),'join',__import__('builtins')._fullarc_qt_slot(lambda:mesh_merge_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_merge')
    import mesh_fill_ui
    action('mesh_fill',tr('メッシュの穴を埋める…','Fill Mesh Holes…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:mesh_fill_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_fill')
    import mesh_harmonize_ui
    action('mesh_harmonize',tr('メッシュ法線を整合…','Harmonize Mesh Normals…'),'surface-reverse',__import__('builtins')._fullarc_qt_slot(lambda:mesh_harmonize_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_harmonize')
    import mesh_reverse_ui
    action('mesh_reverse',tr('メッシュ法線を反転…','Reverse Mesh Normals…'),'surface-reverse',__import__('builtins')._fullarc_qt_slot(lambda:mesh_reverse_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_reverse')
    import mesh_smooth_ui
    action('mesh_smooth',tr('メッシュを平滑化…','Smooth Mesh…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:mesh_smooth_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_smooth')
    import mesh_inspect_ui
    action('mesh_inspect',tr('メッシュを検査…','Inspect Mesh…'),'measure',__import__('builtins')._fullarc_qt_slot(lambda:mesh_inspect_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_inspect')
    import mesh_delete_ui
    action('mesh_delete',tr('メッシュ面を削除…','Delete Mesh Faces…'),'mesh-cut',__import__('builtins')._fullarc_qt_slot(lambda:mesh_delete_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_delete')
    import mesh_components_ui
    action('mesh_components',tr('小さなメッシュ成分を削除…','Remove Small Mesh Components…'),'mesh-separate',__import__('builtins')._fullarc_qt_slot(lambda:mesh_components_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_components')
    import mesh_refine_ui
    action('mesh_refine',tr('メッシュを細分化…','Refine Mesh…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:mesh_refine_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_refine')
    import mesh_reduce_ui
    action('mesh_reduce',tr('メッシュ面数を削減…','Reduce Mesh Facets…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:mesh_reduce_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('mesh_reduce')
    action('mesh_separate',tr('部品を分離…','Separate Parts…'),'mesh-separate',__import__('builtins')._fullarc_qt_slot(lambda:ws.edit_mesh('separate'),(0, 0, False, False)))
    action('mesh_cut',tr('平面で切断…','Plane Cut…'),'mesh-cut',__import__('builtins')._fullarc_qt_slot(lambda:ws.edit_mesh('cut'),(0, 0, False, False)))
    ws.solid_action_keys.extend(['mesh_separate','mesh_cut'])
    action('align',tr('位置合わせ…'),'align',ws.align)
    ws.ribbon_actions['align'].setToolTip(tr('頂点どうし、平面どうし、円筒の軸どうしを位置合わせします。',
                                           'Align two vertices, two planar faces or two cylinder axes.'))
    action('join',tr('結合'),'Part_Fuse',__import__('builtins')._fullarc_qt_slot(lambda: ws.boolean(False),(0, 0, False, False)))
    action('cut',tr('切り取り'),'Part_Cut',__import__('builtins')._fullarc_qt_slot(lambda: ws.boolean(True),(0, 0, False, False)))
    action('intersect',tr('交差部分を残す','Intersect'),'Part_Common',__import__('builtins')._fullarc_qt_slot(lambda:ws.boolean('intersect'),(0, 0, False, False)))
    ws.solid_action_keys.append('intersect')
    action('component',tr('コンポーネントを作成…','Create Components…'),'component',ws.create_component)
    action('duplicate_component',tr('コンポーネントを複製','Duplicate Component'),'component',ws.duplicate_component)
    action('ground_component',tr('接地 / 接地を解除','Ground / Unground'),'rigid-joint',ws.ground_component)
    action('rigid_joint',tr('固定ジョイント…','Rigid Joint…'),'rigid-joint',__import__('builtins')._fullarc_qt_slot(lambda:ws.start_joint('rigid'),(0, 0, False, False)))
    action('revolute_joint',tr('回転ジョイント…','Revolute Joint…'),'revolute-joint',__import__('builtins')._fullarc_qt_slot(lambda:ws.start_joint('revolute'),(0, 0, False, False)))
    action('slider_joint',tr('スライダージョイント…','Slider Joint…'),'slider-joint',__import__('builtins')._fullarc_qt_slot(lambda:ws.start_joint('slider'),(0, 0, False, False)))
    action('cylindrical_joint',tr('円筒ジョイント…','Cylindrical Joint…'),'revolute-joint',__import__('builtins')._fullarc_qt_slot(lambda:ws.start_joint('cylindrical'),(0, 0, False, False)))
    action('ball_joint',tr('ボールジョイント…','Ball Joint…'),'revolute-joint',__import__('builtins')._fullarc_qt_slot(lambda:ws.start_joint('ball'),(0, 0, False, False)))
    import motion_link_ui
    import linear_motion_ui
    action('linear_motion_link',tr('回転と直線移動の連動…','Rotary-Linear Motion Link…'),'slider-joint',__import__('builtins')._fullarc_qt_slot(lambda:linear_motion_ui.show(ws),(0, 0, False, False)))
    action('motion_link',tr('回転比のモーションリンク…','Rotational Motion Link…'),'revolute-joint',__import__('builtins')._fullarc_qt_slot(lambda:motion_link_ui.show(ws),(0, 0, False, False)))
    action('release_joint',tr('ジョイントを解除','Release Joint'),'rigid-joint',ws.release_joint)
    ws.solid_action_keys.extend(['component','duplicate_component','ground_component','rigid_joint','revolute_joint','slider_joint','cylindrical_joint','ball_joint','motion_link','linear_motion_link','release_joint'])
    action('export',tr('エクスポート…'),'document-export',ws.export).setToolTip(
        tr('表示中の形状をすべて書き出します。対象外にする形状は非表示にしてください。',
           'Export all visible geometry. Hide objects you want to exclude.'))
    action('insert',tr('挿入…'),'insert',command('Std_Import'))
    action('insert_native',tr('FluxCAD部品を挿入…','Insert FluxCAD Part…'),'insert',__import__('builtins')._fullarc_qt_slot(lambda:insert_native_document(ws),(0, 0, False, False)))
    action('search',tr('コマンドを検索'),'search',ws.command_search,'S')
    action('select',tr('選択'),'select',ws.select_mode)
    action('box_select',tr('窓選択'),'select',command('Std_BoxSelection'))
    action('select_all',tr('すべて選択'),'select',command('Std_SelectAll'))
    action('visible_solids',tr('表示中のソリッドを選択','Select Visible Solids'),'select',__import__('builtins')._fullarc_qt_slot(lambda:select_visible(ws,'solid'),(0, 0, False, False)))
    action('visible_meshes',tr('表示中のメッシュを選択','Select Visible Meshes'),'select',__import__('builtins')._fullarc_qt_slot(lambda:select_visible(ws,'mesh'),(0, 0, False, False)))
    action('invert_visible',tr('表示中の選択を反転','Invert Visible Selection'),'select',__import__('builtins')._fullarc_qt_slot(lambda:invert_visible(ws),(0, 0, False, False))).setToolTip(tr('表示中のソリッドとメッシュだけで選択を反転します。','Invert selection among visible solids and meshes only.'))
    import named_views
    action('named_views',tr('名前付きビュー…','Named Views…'),'view-axonometric',__import__('builtins')._fullarc_qt_slot(lambda:named_views.show(ws),(0, 0, False, False)))
    action('fit',tr('全体表示'),'zoom-fit-best',ws.fit)
    import look_at_face
    action('look_at_face',tr('選択面を正面表示','Look At Face'),'align-to-selection',__import__('builtins')._fullarc_qt_slot(lambda:look_at_face.show(ws),(0, 0, False, False))).setToolTip(tr('平面を1面選択します。近い側から面に垂直な向きへ回転し、ズームは保持します。','Select one planar face. Rotate normal to it from the nearer side, retaining zoom.'))
    action('fit_selection',tr('選択物を拡大表示','Fit Selection'),'zoom-fit-best',__import__('builtins')._fullarc_qt_slot(lambda:fit_selection(ws),(0, 0, False, False))).setToolTip(tr('選択した形状に表示を合わせます。向き・形状・配置は保持します。','Fit the view to selected geometry, preserving orientation, geometry and placement.'))
    tabs_action = action('bottom_tabs',tr('下段タブを表示'),'eye',ws.toggle_bottom_tabs)
    tabs_action.setCheckable(True)
    tabs_action.setChecked(ws.bottom_tabs_visible)
    tabs_action.setToolTip(tr('下段のドキュメントタブと加工履歴をまとめて表示 / 非表示'))
    action('native',tr('FreeCAD 標準UIに戻す'),'preferences-system',ws.restore)
    ws.sketch_action_keys = []
    sketch_commands = [
        ('line',tr('線分'),'line','Sketcher_CreateLine'),
        ('polyline',tr('ポリライン'),'polyline','Sketcher_CreatePolyline'),
        ('draw_rectangle',tr('2点指定の長方形'),'Sketcher_CreateRectangle','Sketcher_CreateRectangle'),
        ('center_rectangle',tr('中心の長方形'),'center-rectangle','Sketcher_CreateRectangle_Center'),
        ('rounded_rectangle',tr('角丸長方形','Rounded Rectangle'),'sketch-fillet','Sketcher_CreateOblong'),
        ('circle',tr('中心と半径の円'),'circle','Sketcher_CreateCircle'),
        ('circle3',tr('3点指定の円'),'circle3','Sketcher_Create3PointCircle'),
        ('arc',tr('中心指定の円弧'),'arc','Sketcher_CreateArc'),
        ('arc3',tr('3点指定の円弧'),'arc3','Sketcher_Create3PointArc'),
        ('spline',tr('フィット点スプライン'),'spline','Sketcher_CreateBSplineByInterpolation'),
        ('control_spline',tr('制御点スプライン'),'spline','Sketcher_CreateBSpline'),
        ('ellipse',tr('楕円'),'ellipse','Sketcher_CreateEllipseByCenter'),
        ('polygon',tr('ポリゴン'),'polygon','Sketcher_CreateRegularPolygon'),
        ('slot',tr('スロット'),'slot','Sketcher_CreateSlot'),
        ('arc_slot',tr('円弧スロット','Arc Slot'),'slot','Sketcher_CreateArcSlot'),
        ('point',tr('点'),'point','Sketcher_CreatePoint'),
        ('sketch_mirror',tr('ミラー'),'mirror','Sketcher_Symmetry'),
        ('sketch_rectangular_pattern',tr('矩形状パターン','Rectangular Pattern'),'linear-pattern','Sketcher_RectangularArray'),
        ('sketch_rotate',tr('回転 / 円形状パターン','Rotate / Circular Pattern'),'circular-pattern','Sketcher_Rotate'),
        ('sketch_move',tr('移動 / 配列','Move / Array'),'move','Sketcher_Translate'),
        ('sketch_copy',tr('コピー','Copy'),'document-copy','Sketcher_Copy'),
        ('sketch_scale',tr('尺度','Scale'),'mesh-scale','Sketcher_Scale'),
        ('project',tr('投影','Project'),'sketch-project','Sketcher_Projection'),
        ('sketch_intersection',tr('交差','Intersect'),'sketch-intersection','Sketcher_Intersection'),
        ('trim',tr('トリム'),'trim','Sketcher_Trimming'),
        ('extend',tr('延長'),'extend','Sketcher_Extend'),
        ('sketch_split',tr('分割','Split Edge'),'trim','Sketcher_Split'),
        ('sketch_offset',tr('オフセット'),'offset','Sketcher_Offset'),
        ('sketch_fillet',tr('フィレット'),'sketch-fillet','Sketcher_CreateFillet'),
        ('sketch_chamfer',tr('面取り'),'chamfer','Sketcher_CreateChamfer'),
        ('construction',tr('補助線に切替'),'construction','Sketcher_ToggleConstruction'),
        ('coincident',tr('一致'),'coincident','Sketcher_ConstrainCoincident'),
        ('point_on_object',tr('点を線上に拘束','Point on Object'),'point-on-object','Sketcher_ConstrainPointOnObject'),
        ('horizontal',tr('水平'),'horizontal','Sketcher_ConstrainHorizontal'),
        ('vertical',tr('垂直'),'vertical','Sketcher_ConstrainVertical'),
        ('parallel',tr('平行'),'parallel','Sketcher_ConstrainParallel'),
        ('perpendicular',tr('直角'),'perpendicular','Sketcher_ConstrainPerpendicular'),
        ('equal',tr('等しい'),'equal','Sketcher_ConstrainEqual'),
        ('tangent',tr('接線'),'tangent','Sketcher_ConstrainTangent'),
        ('symmetric',tr('対称'),'symmetric','Sketcher_ConstrainSymmetric'),
        ('fix',tr('固定'),'fix','Sketcher_ConstrainBlock'),
        ('dimension',tr('寸法'),'dimension','Sketcher_Dimension'),
        ('dimension_length',tr('長さ・距離','Length / Distance'),'dimension','Sketcher_ConstrainDistance'),
        ('dimension_horizontal',tr('水平距離','Horizontal Distance'),'dimension','Sketcher_ConstrainDistanceX'),
        ('dimension_vertical',tr('垂直距離','Vertical Distance'),'dimension-vertical','Sketcher_ConstrainDistanceY'),
        ('dimension_radius',tr('半径','Radius'),'dimension-radius','Sketcher_ConstrainRadius'),
        ('dimension_diameter',tr('直径','Diameter'),'dimension-diameter','Sketcher_ConstrainDiameter'),
        ('dimension_angle',tr('角度','Angle'),'dimension-angle','Sketcher_ConstrainAngle'),
        ('reference_dimension',tr('駆動寸法 / 参照寸法に切替','Toggle Driving / Reference Dimension'),'dimension-reference','Sketcher_ToggleDrivingConstraint')]
    ws.sketch_commands={key:cmd for key,title,icon,cmd in sketch_commands}
    for key,title,icon,cmd in sketch_commands:
        action(key,title,icon,__import__('builtins')._fullarc_qt_slot(lambda c=cmd: ws.sketch_command(c),(1, 0, False, False)))
        ws.sketch_action_keys.append(key)
    import spline_knot_ui
    action('spline_insert_knot',tr('スプラインに制御点を追加…','Insert Spline Control Point…'),'Sketcher_BSplineInsertKnot',__import__('builtins')._fullarc_qt_slot(lambda:spline_knot_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('spline_insert_knot')
    import spline_degree_ui
    action('spline_increase_degree',tr('スプラインの次数を1つ上げる…','Increase Spline Degree by One…'),'Sketcher_BSplineIncreaseDegree',__import__('builtins')._fullarc_qt_slot(lambda:spline_degree_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('spline_increase_degree')
    import spline_reduce_ui
    action('spline_decrease_degree',tr('スプラインの次数を1つ下げる…','Decrease Spline Degree by One…'),'Sketcher_BSplineDecreaseDegree',__import__('builtins')._fullarc_qt_slot(lambda:spline_reduce_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('spline_decrease_degree')
    import sketch_control_polygon
    action('spline_control_polygon',tr('制御ポリゴン表示を切替（全スケッチ共通）','Toggle Control Polygon (All Sketches)'),'Sketcher_BSplinePolygon',__import__('builtins')._fullarc_qt_slot(lambda:sketch_control_polygon.toggle(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('spline_control_polygon')
    import sketch_comb
    action('spline_comb',tr('曲率コーム表示を切替（全スケッチ共通）','Toggle Curvature Comb (All Sketches)'),'Sketcher_BSplineComb',__import__('builtins')._fullarc_qt_slot(lambda:sketch_comb.toggle(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('spline_comb')
    import elliptical_arc_ui
    action('elliptical_arc',tr('楕円弧…','Elliptical Arc…'),'ellipse',__import__('builtins')._fullarc_qt_slot(lambda:elliptical_arc_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('elliptical_arc')
    import circumscribed_polygon_ui
    action('circumscribed_polygon',tr('外接ポリゴン…','Circumscribed Polygon…'),'polygon',__import__('builtins')._fullarc_qt_slot(lambda:circumscribed_polygon_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('circumscribed_polygon')
    import midpoint_line_ui
    action('midpoint_line',tr('中点から線分…','Midpoint Line…'),'line',__import__('builtins')._fullarc_qt_slot(lambda:midpoint_line_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('midpoint_line')
    import conic_ui
    action('conic_curve',tr('円錐曲線…','Conic Curve…'),'spline',__import__('builtins')._fullarc_qt_slot(lambda:conic_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('conic_curve')
    import ellipse_dimensions
    action('ellipse_dimensions',tr('楕円：横幅・縦高さ…','Ellipse: Width / Height…'),'ellipse',__import__('builtins')._fullarc_qt_slot(lambda:ellipse_dimensions.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('ellipse_dimensions')
    import ellipse_resize_ui
    action('ellipse_resize',tr('楕円の横幅・縦高さを変更…','Resize Ellipse…'),'ellipse',__import__('builtins')._fullarc_qt_slot(lambda:ellipse_resize_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('ellipse_resize')
    import ellipse_center_ui
    action('ellipse_center',tr('楕円の中心位置を変更…','Move Ellipse Center…'),'ellipse',__import__('builtins')._fullarc_qt_slot(lambda:ellipse_center_ui.show(ws),(0, 0, False, False)))
    ws.sketch_action_keys.append('ellipse_center')
    for key, tip in {
        'project': tr('別のスケッチやボディの辺・頂点を編集中の平面へ投影します。元の形状の変更に追従します。',
                      'Project edges or vertices from another sketch or body onto the sketch plane. References follow source changes.'),
        'sketch_intersection': tr('ボディの面・辺とスケッチ平面の交差を取り込みます。投影とは異なり、平面を横切る形状を選びます。',
                                  'Include intersections of faces or edges with the sketch plane. Select geometry crossing the plane.'),
        'dimension': tr('線・円・円弧などの選択に応じて寸法を付けます。Mキーで寸法の種類を切り替えます。',
                        'Dimension selected lines, circles or arcs contextually. Press M to cycle dimension types.'),
        'point_on_object': tr('点と線・円弧などをCtrlで選択して、点をその曲線上に拘束します。投影した辺も参照できます。',
                              'Ctrl-select a point and a line or curve to constrain the point onto it. Projected edges can be used.'),
        'reference_dimension': tr('選択した寸法を、形状を決める駆動寸法と測定用の参照寸法の間で切り替えます。',
                                  'Switch selected dimensions between driving the geometry and measuring it as a reference.'),
        'sketch_mirror': tr('スケッチの線・円などを選択し、鏡映の基準となる軸を指定して複製します。',
                            'Select sketch geometry, then choose the reflection axis to create a mirrored copy.'),
        'sketch_rectangular_pattern': tr('選択したスケッチ図形を行・列に複製します。個数や寸法はFreeCAD標準の設定画面で指定します。',
                                         'Repeat selected sketch geometry in rows and columns using the native FreeCAD settings.'),
        'sketch_rotate': tr('スケッチ図形を選択して回転します。複製数を増やすと円形状パターンを作成できます。',
                            'Rotate selected sketch geometry. Increase the copy count to create a circular pattern.'),
        'sketch_move': tr('スケッチ図形を選択し、基準点と移動先をクリックします。操作パネルで複製数と行数を指定できます。',
                          'Select sketch geometry, then click a base point and destination. Set copy and row counts in the task controls.'),
        'sketch_copy': tr('選択したスケッチ図形をコピーします。基準点を最後に選択し、コピー先をクリックします。',
                          'Copy selected sketch geometry. Select the reference point last, then click the destination.'),
        'sketch_scale': tr('選択したスケッチ図形を、基準点と倍率を指定して拡大・縮小します。',
                           'Scale selected sketch geometry using a reference point and scale factor.'),
    }.items():
        ws.ribbon_actions[key].setToolTip(tip)
    action('edit_sketch',tr('スケッチを編集'),'Sketcher_NewSketch',ws.edit_sketch)
    action('validate_sketch',tr('スケッチを検証・修復…','Validate / Repair Sketch…'),
           'check-geometry',ws.validate_sketch).setToolTip(tr(
               '端点の一致不足や不正な拘束をFreeCAD標準ツールで検査します。編集中なら編集を終了して開きます。修正は検査後に実行します。',
               'Inspect missing coincidences and invalid constraints with FreeCAD. Ends sketch editing when necessary. Repairs run only when requested in the inspector.'))
    action('select_sketch',tr('選択（作図を終了）'),'select',ws.select_sketch_geometry)
    ws.sketch_action_keys.append('select_sketch')
    action('finish_sketch',tr('スケッチを終了'),'finish',ws.finish_sketch)
    ws.sketch_action_keys.append('finish_sketch')

    def measure():
        import model_mesh, model
        selected = Gui.Selection.getSelection()
        if len(selected) > 1:
            if any((obj.Document != App.ActiveDocument or model_mesh.is_mesh(obj) or (not hasattr(obj, 'Shape')) or getattr(obj, 'FluxCADInternal', False) for obj in selected)):
                raise ValueError(tr('同じ文書のソリッドボディだけを選択してください。', 'Select only solid bodies in the active document.'))
            shapes = [model.world_shape(obj) for obj in selected]
            if any((shape.isNull() or not shape.isValid() or (not shape.Solids) for shape in shapes)):
                raise ValueError(tr('有効なソリッドボディだけを選択してください。', 'Select only valid solid bodies.'))
            bounds = App.BoundBox()
            for shape in shapes:
                bounds.add(shape.BoundBox)
            text = tr('選択ボディ：%d\n全体外形 X / Y / Z\n%.3f / %.3f / %.3f mm\n\n体積合計  %.3f mm³\n表面積合計  %.3f mm²\n\n重なり部分は各ボディ分を合計します。', 'Selected bodies: %d\nCombined bounds X / Y / Z\n%.3f / %.3f / %.3f mm\n\nSum of volumes  %.3f mm³\nSum of areas  %.3f mm²\n\nOverlaps are counted separately for each body.') % (len(shapes), bounds.XLength, bounds.YLength, bounds.ZLength, sum((shape.Volume for shape in shapes)), sum((shape.Area for shape in shapes)))
            if len(shapes) == 2:
                import math
                distance = float(shapes[0].distToShape(shapes[1])[0])
                if not math.isfinite(distance) or distance < 0:
                    raise ValueError(tr('最短距離を計算できません。', 'Cannot calculate the minimum distance.'))
                text += tr('\n\n最短距離  %.6f mm\n接触・干渉の区別は「干渉チェック」で確認してください。', '\n\nMinimum distance  %.6f mm\nUse Interference to distinguish contact and overlap.') % distance
            W.QMessageBox.information(ws.main, tr('複数ボディを計測', 'Measure Multiple Bodies'), text)
            return
        if len(selected) == 1 and model_mesh.is_mesh(selected[0]):
            obj = selected[0]
            mesh = model_mesh.world_mesh(obj)
            b = mesh.BoundBox
            W.QMessageBox.information(ws.main, tr('検査 — ') + obj.Label, tr('外形寸法 X / Y / Z\n%.3f / %.3f / %.3f mm\n\n三角形数：%d', 'Bounding size X / Y / Z\n%.3f / %.3f / %.3f mm\n\nTriangles: %d') % (b.XLength, b.YLength, b.ZLength, mesh.CountFacets))
            return
        obj = ws.selection()[0]
        shape = model.world_shape(obj)
        b = shape.BoundBox
        W.QMessageBox.information(ws.main, tr('検査 — ') + obj.Label, tr('外形寸法 X / Y / Z\n%.3f / %.3f / %.3f mm\n\n体積  %.3f mm³\n表面積  %.3f mm²') % (b.XLength, b.YLength, b.ZLength, shape.Volume, shape.Area))
    action('measure',tr('計測（寸法・体積）'),'measure',measure)
    import native_tools
    for key,label,english,icon,tip,tip_en in [
        ('native_measure','計測','Measure','measure',
         '辺・面・点を選択して計測します。Ctrlで2つ選択すると距離や角度を測れます。',
         'Measure selected edges, faces or points. Ctrl-select two elements for distance or angle.'),
        ('check_geometry','形状を検査','Check Geometry','check-geometry',
         '選択した形状をFreeCAD標準の検査ツールで検証します。',
         'Validate selected shapes with the native FreeCAD geometry checker.'),
        ('solid_scale','尺度','Scale','mesh-scale',
         '選択した形状を原点基準で拡大・縮小します。均一倍率またはXYZ別の倍率を指定できます。',
         'Scale selected shapes about the origin, uniformly or with separate X/Y/Z factors.'),
        ('appearance','外観','Appearance','appearance',
         '選択したボディ・メッシュの色、透明度、表示方法を設定します。',
         'Set color, transparency and display style for selected bodies or meshes.')]:
        action(key,tr(label,english),icon,__import__('builtins')._fullarc_qt_slot(lambda k=key:native_tools.start(ws,k),(1, 0, False, False))).setToolTip(tr(tip,tip_en))
        ws.solid_action_keys.append(key)
    for key,label,english,icon,tip,tip_en in [
        ('surface_patch','パッチ','Patch','surface-patch',
         '閉じた境界の辺を選び、面を張ります。閉じたスケッチ全体の事前選択も使えます。',
         'Fill a closed boundary with a surface. Preselect its edges or an entire closed sketch.'),
        ('surface_boundary','境界サーフェス','Boundary Surface','surface-boundary',
         '2〜4本の境界曲線から面を作成します。張り方を標準タスクで指定します。',
         'Create a surface from 2 to 4 boundary curves. Choose the filling style in the native task.'),
        ('surface_sections','断面曲線から面','Surface from Sections','loft',
         '複数の辺を順番に選択し、それらを通る面を作成します。1断面につき1本の辺を使います。',
         'Create a surface through selected edges in order, using one edge per section.'),
        ('cross_sections','断面線を作成','Create Cross Sections','cross-sections',
         '選択形状からXY・XZ・YZ方向の断面線を作成します。複数断面の間隔も指定できます。',
         'Create XY, XZ or YZ section curves from selected shapes, with optional repeated spacing.'),
        ('section_analysis','断面解析（クリッピング）','Section Analysis (Clipping)','section-analysis',
         '形状を変更せず、切断位置より手前を非表示にして内部を確認します。',
         'Inspect the interior with view clipping, without modifying the shape.')]:
        action(key,tr(label,english),icon,__import__('builtins')._fullarc_qt_slot(lambda k=key:native_tools.start(ws,k),(1, 0, False, False))).setToolTip(tr(tip,tip_en))
        ws.solid_action_keys.append(key)

    import ruled_strip_ui
    action('ruled_strip',tr('辺から線織面…','Ruled Surface From Edge…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:ruled_strip_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('ruled_strip')

    import surface_copy_ui
    action('surface_copy',tr('選択面をコピー…','Copy Selected Faces…'),'surface-offset',__import__('builtins')._fullarc_qt_slot(lambda:surface_copy_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_copy')

    import natural_untrim_ui
    action('natural_untrim',tr('面の自然境界を復元…','Restore Natural Surface Boundary…'),'surface-extend',__import__('builtins')._fullarc_qt_slot(lambda:natural_untrim_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('natural_untrim')

    import edge_comb_ui
    action('edge_comb',tr('辺の曲率コーム解析…','Edge Curvature Comb Analysis…'),'Sketcher_BSplineComb',__import__('builtins')._fullarc_qt_slot(lambda:edge_comb_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('edge_comb')

    import surface_curvature_ui
    action('surface_curvature',tr('面の曲率標本解析…','Surface Curvature Samples…'),'Sketcher_BSplineComb',__import__('builtins')._fullarc_qt_slot(lambda:surface_curvature_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_curvature')

    import draft_analysis_ui
    action('draft_analysis',tr('面の抜き勾配標本解析…','Surface Draft Angle Samples…'),'Sketcher_BSplineComb',__import__('builtins')._fullarc_qt_slot(lambda:draft_analysis_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('draft_analysis')

    import surface_ops
    for key,label,english,icon,tip,tip_en in [
        ('surface_extrude','押し出し','Extrude','extrude',
         'スケッチや輪郭線を押し出して面を作成します。両端はふさぎません。',
         'Extrude sketches or curves into surfaces without end caps.'),
        ('surface_revolve','回転','Revolve','revolve',
         '輪郭線を指定軸のまわりに回転させ、面を作成します。',
         'Revolve a profile about an axis to create a surface.'),
        ('surface_loft','ロフト','Loft','loft',
         '複数の開いた／閉じた輪郭を順番につなぎ、面を作成します。',
         'Create a surface through ordered open or closed profiles.'),
        ('surface_sweep','スイープ','Sweep','sweep',
         '断面を選び、タスク内の「スイープ経路」で経路を指定します。',
         'Choose a profile, then use Sweep Path in the task to select the path.'),
        ('surface_extend','面を延長','Extend Face','surface-extend',
         '面を1つ選び、U・V方向の延長率を指定します。プレビュー・再編集ができます。',
         'Select one face and enter U/V extension percentages, with preview and later editing.')]:
        action(key,tr(label,english),icon,__import__('builtins')._fullarc_qt_slot(lambda k=key:surface_ops.start(ws,k),(1, 0, False, False))).setToolTip(tr(tip,tip_en))
        ws.solid_action_keys.append(key)

    import surface_finish
    import reverse_normal_ui
    action('reverse_normal',tr('法線を反転…','Reverse Normal…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:reverse_normal_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('reverse_normal')
    import untrim_ui
    action('surface_untrim',tr('面の内側穴を埋める…','Fill Internal Surface Holes…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:untrim_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_untrim')
    import unstitch_ui
    action('surface_unstitch',tr('全ての面を分離…','Unstitch All Faces…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:unstitch_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_unstitch')
    import projection_ui
    action('surface_projection',tr('曲面へ投影…','Project to Surface…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:projection_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_projection')
    import isocurve_ui
    action('surface_isocurve',tr('等パラメータ曲線を抽出…','Extract Isoparametric Curve…'),'surface-section',__import__('builtins')._fullarc_qt_slot(lambda:isocurve_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_isocurve')
    import trim_ui
    action('surface_trim',tr('面をトリム…','Trim Surface…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:trim_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_trim')
    import stitch_ui
    action('surface_stitch',tr('面を縫合…','Stitch Surfaces…'),'surface-patch',__import__('builtins')._fullarc_qt_slot(lambda:stitch_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('surface_stitch')
    action('surface_offset',tr('オフセット面','Offset Surface'),'surface-offset',__import__('builtins')._fullarc_qt_slot(lambda:surface_finish.offset(ws),(0, 0, False, False))).setToolTip(
        tr('サーフェス、またはボディの選択面を法線方向に一定距離ずらします。',
           'Offset a surface or selected body faces by a signed normal distance.'))
    action('surface_thicken',tr('厚み付け','Thicken'),'surface-thicken',__import__('builtins')._fullarc_qt_slot(lambda:surface_finish.offset(ws,fill=True),(0, 0, False, False))).setToolTip(
        tr('サーフェスに厚みを付け、新しいボディを作成します。正負の距離で方向を指定します。',
           'Thicken a surface into a new body. Signed distance controls the direction.'))
    action('refine_shape',tr('形状を簡略化','Refine Shape'),'refine-shape',__import__('builtins')._fullarc_qt_slot(lambda:surface_finish.refine(ws),(0, 0, False, False))).setToolTip(
        tr('同じ面上の不要な分割線などを除きます。元形状への参照を保持します。',
           'Remove redundant splits such as coplanar edges, keeping a link to the source.'))
    ws.solid_action_keys.extend(['surface_offset','surface_thicken','refine_shape'])

    def axes():
        if Gui.activeDocument():
            v = Gui.activeDocument().activeView()
            v.setAxisCross(not v.hasAxisCross())
    action('axes',tr('原点軸を表示 / 非表示'),'Part_Box',axes)
    grid_action = action('grid',tr('グリッド'),'grid',ws.toggle_grid)
    grid_action.setCheckable(True)
    grid_action.setChecked(ws.grid.enabled)
    grid_action.setToolTip(tr('作図面のグリッドを表示 / 非表示。細かさや固定間隔は「グリッド設定」で変更できます。'))
    action('grid_settings',tr('グリッド設定…'),'grid',ws.grid_settings)
    for key,text,method in [('top',tr('上面'),'viewTop'),('front',tr('正面'),'viewFront'),('right',tr('右側面'),'viewRight')]:
        action(key,text,'Part_Box',__import__('builtins')._fullarc_qt_slot(lambda m=method: getattr(Gui.activeDocument().activeView(),m)() if Gui.activeDocument() else None,(1, 0, False, False)))

    def button(parent_layout, a, large=False, compact=False):
        b = W.QToolButton()
        b.setDefaultAction(a)
        b.setIconSize(QtCore.QSize(26,26) if large else QtCore.QSize(16,16))
        b.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        if large:
            b.setFixedSize(40,34)
        if compact:
            b.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            b.setFixedSize(40,34)
        b.setObjectName('FluxIcon_'+a.text())
        parent_layout.addWidget(b)
        return b

    top = W.QFrame()
    top.setObjectName('FluxTop')
    row = W.QHBoxLayout(top)
    row.setContentsMargins(10,0,10,0)
    row.setSpacing(4)
    brand = W.QLabel('FullArc<span style="color:#1689bf">CAD</span>')
    brand.setObjectName('FullArcCADBrand')
    brand.setStyleSheet('font-size:16px;font-weight:700;margin-right:16px;')
    row.addWidget(brand)
    file_button = W.QToolButton()
    file_button.setText(tr('ファイル'))
    file_menu = W.QMenu(file_button)
    file_menu.setObjectName('FluxFileMenu')
    for key in ['new','open','solidworks_open','solidworks_brep_open','examples','example_guide','save','save_as','export']:
        file_menu.addAction(ws.ribbon_actions[key])
    file_button.setMenu(file_menu)
    import recent_files
    recent_files.install(ws, file_menu)
    file_button.setPopupMode(W.QToolButton.InstantPopup)
    row.addWidget(file_button)
    for key in ['save','undo','redo']:
        button(row,ws.ribbon_actions[key])
    row.addStretch()
    ws.doc_title = W.QLabel(tr('無題のデザイン'))
    ws.doc_title.setObjectName('FluxDocTitle')
    row.addWidget(ws.doc_title)
    row.addStretch()
    options = W.QToolButton()
    options.setText(tr('設定 ▾'))
    menu = W.QMenu(options)
    menu.setObjectName('FluxSettingsMenu')
    gltf_action=menu.addAction(tr('glTF 表示設定（材質・アニメーション）…'))
    gltf_action.setObjectName('FullArcCAD_glTFControlsAction')
    gltf_action.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda:ws.safe(__import__('builtins')._fullarc_qt_slot(lambda:__import__('gltf_controls').show_current(),(0, 0, False, False))),(0, 0, False, False)))
    import i18n
    language_menu=W.QMenu(tr('表示言語 / Language','Language'),menu)
    language_menu.setObjectName('FluxSettingsLanguage');menu.addMenu(language_menu)
    ws.ribbon_menus['language']=language_menu
    ws.language_action_group=QtGui.QActionGroup(language_menu)
    ws.language_action_group.setExclusive(True);ws.language_actions={}
    for code,title in i18n.available_languages():
        entry=language_menu.addAction(title);entry.setCheckable(True)
        entry.setChecked(i18n.pending_language()==code);entry.setData(code)
        ws.language_action_group.addAction(entry);ws.language_actions[code]=entry
        entry.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False,c=code:ws.change_language(c),(2, 0, False, False)))
    view_menu=W.QMenu(tr('表示'),menu);view_menu.setObjectName('FluxSettingsView');menu.addMenu(view_menu)
    ws.ribbon_menus['設定.表示']=view_menu
    for key in ['fit','fit_selection','look_at_face','grid','grid_settings','axes','bottom_tabs','top','front','right']:view_menu.addAction(ws.ribbon_actions[key])
    menu.addAction(ws.ribbon_actions['bottom_tabs'])
    native_menu = menu.addAction(tr('FreeCAD メニューバーを表示 / 非表示'))
    native_menu.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda: ws.main.menuBar().setVisible(not ws.main.menuBar().isVisible()),(0, 0, False, False)))
    nav_menu = W.QMenu(tr('マウス操作'),menu);nav_menu.setObjectName('FluxSettingsMouse');menu.addMenu(nav_menu)
    ws.ribbon_menus['設定.マウス操作']=nav_menu
    for title,key,value in [(tr('自由回転'),'FreeOrbit',ws.mouse.free_orbit),(tr('ズーム方向を反転'),'ReverseZoom',ws.mouse.reverse_zoom)]:
        option = nav_menu.addAction(title)
        option.setCheckable(True)
        option.setChecked(value)
        option.toggled.connect(__import__('builtins')._fullarc_qt_slot(lambda enabled,k=key: ws.mouse.preference(k,enabled),(2, 1, False, False)))
    menu.addAction(ws.ribbon_actions['native'])
    options.setMenu(menu)
    options.setPopupMode(W.QToolButton.InstantPopup)
    row.addWidget(options)
    layout.addWidget(top)
    top.setFixedHeight(26)

    body=W.QHBoxLayout();body.setContentsMargins(10,0,4,0);body.setSpacing(10)
    workspace=W.QToolButton();workspace.setObjectName('FluxWorkspace');workspace.setText(tr('デザイン'))
    ws.workspace_button=workspace;ws.drawing_mode=False
    workspace.setFixedSize(94,62)
    workspace_menu=W.QMenu(workspace)
    workspace_menu.setObjectName('FluxWorkspaceMenu')
    build_workspace_menu(ws,workspace_menu,tr)
    workspace.setMenu(workspace_menu);workspace.setPopupMode(W.QToolButton.InstantPopup)
    body.addWidget(workspace)
    right=W.QVBoxLayout();right.setContentsMargins(0,0,0,0);right.setSpacing(0)
    tabrow = W.QHBoxLayout();tabrow.setContentsMargins(0,0,0,0)
    ws.ribbon_tabs = W.QTabBar()
    ws.ribbon_tabs.setFixedHeight(26)
    ws.ribbon_tabs.setExpanding(False);ws.ribbon_tabs.setDrawBase(False)
    ws.tab_indices={'solid':0,'surface':1,'mesh':2,'sheet':3,'plastic':4,'manage':5,'utilities':6,'sketch':7,'drawing':8}
    for name in [tr('ソリッド'),tr('サーフェス'),tr('メッシュ'),tr('シートメタル'),tr('プラスチック'),tr('管理'),tr('ユーティリティ'),tr('スケッチ'),tr('図面','Drawing')]:
        ws.ribbon_tabs.addTab(name)
    ws.ribbon_tabs.setTabVisible(ws.tab_indices['sketch'],False)
    ws.ribbon_tabs.setTabVisible(ws.tab_indices['drawing'],False)
    ws.ribbon_tabs.setSizePolicy(W.QSizePolicy.Expanding,W.QSizePolicy.Fixed)
    tabrow.addWidget(ws.ribbon_tabs,1)
    button(tabrow,ws.ribbon_actions['search'])
    right.addLayout(tabrow)
    ws.ribbon_stack = W.QStackedWidget()
    ws.ribbon_stack.setFixedHeight(54)
    ws.ribbon_stack.setSizePolicy(W.QSizePolicy.Ignored,W.QSizePolicy.Fixed)
    right.addWidget(ws.ribbon_stack);body.addLayout(right,1);layout.addLayout(body)

    def populate(menu,keys,path):
        # Keep Python wrappers alive across native workbench switches (PySide 6).
        ws.ribbon_menus[path]=menu
        menu.setObjectName('FluxMenu_'+path)
        for key in keys:
            if key is None:menu.addSeparator()
            elif isinstance(key,tuple):
                title,children=key
                submenu=W.QMenu(title,menu);menu.addMenu(submenu)
                populate(submenu,children,path+' > '+title)
            else:
                a=ws.ribbon_actions[key];menu.addAction(a)
                if not a.property('FluxMenuPath'):a.setProperty('FluxMenuPath',path)

    def page(name,groups, compact=False):
        page = W.QWidget()
        row = W.QHBoxLayout(page)
        row.setContentsMargins(0,0,0,0)
        row.setSpacing(5)
        for title, keys, featured in groups:
            frame = W.QFrame()
            frame.setObjectName('FluxGroup')
            group = W.QVBoxLayout(frame)
            group.setContentsMargins(2,0,7,0)
            group.setSpacing(0)
            icons = W.QHBoxLayout()
            icons.setSpacing(1)
            for key in featured:
                button(icons,ws.ribbon_actions[key],True,compact)
            group.addLayout(icons)
            label = W.QToolButton()
            label.setObjectName('FluxGroupLabel')
            label.setFixedHeight(18)
            label.setText(title)
            dropdown = W.QMenu(label)
            populate(dropdown,keys,name+' > '+title)
            ws.ribbon_menus[name+'.'+title]=dropdown
            label.setMenu(dropdown)
            label.setPopupMode(W.QToolButton.InstantPopup)
            group.addWidget(label,0,QtCore.Qt.AlignHCenter)
            row.addWidget(frame)
        row.addStretch()
        ws.ribbon_stack.addWidget(page)
    action('scale_dimensions',tr('寸法で拡大・縮小…','Resize by Dimensions…'),'mesh-scale',__import__('builtins')._fullarc_qt_slot(lambda:ws.dimension_scale.start(),(0, 0, False, False))).setToolTip(tr('現在寸法を確認し、X・Y・Zの増減量をmmで指定します。','Show current dimensions and enter signed X/Y/Z changes in mm.'))
    action('interference',tr('干渉チェック…','Interference…'),'interference',__import__('builtins')._fullarc_qt_slot(lambda:ws.interference.start(),(0, 0, False, False))).setToolTip(tr('ボディ同士の重なりを赤く表示し、干渉体積を確認します。','Inspect overlapping bodies and show shared volume in red.'))
    ws.solid_action_keys.append('interference')
    import all_edges_fillet_ui
    action('all_edges_fillet',tr('全辺フィレット…','All Edges Fillet…'),'fillet',__import__('builtins')._fullarc_qt_slot(lambda:all_edges_fillet_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('all_edges_fillet')
    import tapered_extrude_ui
    action('tapered_extrude',tr('テーパー押し出し…','Tapered Extrude…'),'extrude',__import__('builtins')._fullarc_qt_slot(lambda:tapered_extrude_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('tapered_extrude')
    import split_face_ui
    action('split_face',tr('面を分割…','Split Face…'),'split',__import__('builtins')._fullarc_qt_slot(lambda:split_face_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('split_face')
    import text_sketch_ui
    action('text_sketch',tr('文字をスケッチ曲線にする…','Text as Sketch Curves…'),'Draft_ShapeString',__import__('builtins')._fullarc_qt_slot(lambda:text_sketch_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('text_sketch')
    import solid_text_ui
    action('solid_text',tr('文字ソリッド…','Solid Text…'),'Draft_ShapeString',__import__('builtins')._fullarc_qt_slot(lambda:solid_text_ui.show(ws),(0, 0, False, False)))
    ws.solid_action_keys.append('solid_text')
    import sheetmetal_bridge
    for kind,ja,en in [('rib', '補強リブ…', 'Reinforcing Rib…'), ('gusset', '三角リブ…', 'Triangular Rib…'), ('boss', '取付ボス…', 'Mounting Boss…'), ('snap', 'スナップフィット爪…', 'Snap-fit Hook…')]:
        action('plastic_'+kind,tr(ja,en),'plastic-'+kind,__import__('builtins')._fullarc_qt_slot(lambda k=kind:ws.plastic.start(k),(1, 0, False, False)))
        ws.solid_action_keys.append('plastic_'+kind)
    # No SheetMetal commands or operation dialogs are registered in this build.
    sheet_keys = ('sheet_base','sheet_flange','sheet_unfold','sheet_contour',
                  'sheet_hem','sheet_fold_line','sheet_corner_relief','sheet_junction')
    sheet_hint = tr('この配布版では板金機能を提供していません。', 'Sheet metal features are unavailable in this release.')
    for key in sheet_keys:
        blocked = action(key, sheet_hint, 'sheet-base', lambda: None)
        blocked.setEnabled(False)
        blocked.setVisible(False)
    page(tr('ソリッド'),[
        (tr('スケッチ'),['sketch','sketch_plane','rectangle','alternating_polygon',None,'edit_sketch','validate_sketch'],['sketch']),
        (tr('作成'),['sketch',None,'extrude','tapered_extrude','revolve','sweep','guided_sweep','fixed_sweep','loft','hole',None,'box','cylinder','sphere','dome','torus','coil','spiral','pipe','solid_text','text_sketch',None,(tr('パターン'),['linear_pattern','circular_pattern','path_pattern']),'mirror'],['extrude','revolve','sweep','loft']),
        (tr('修正'),['fillet','all_edges_fillet','chamfer','shell','face_offset','delete_faces','solid_draft','angle_chamfer','split_face',None,'join','cut','intersect','split_body','refine_shape',None,'move_copy','align','move','move_numeric','solid_scale','scale_dimensions',None,'parameters','appearance'],['fillet','chamfer','shell','join','move_copy']),
        (tr('構築'),['offset_plane','midplane','angled_plane','tangent_plane','offset_point_plane','tangent_point_plane','perpendicular_point_plane','three_point_plane','two_edge_plane','path_plane',None,'coordinate_plane','coordinate_axis','coordinate_point','vertex_point','edge_intersection_point','edge_plane_point','three_plane_point','analytic_center_point','point_along_edge','center_axis','two_point_axis','two_plane_axis','normal_point_axis','edge_axis'],['offset_plane','coordinate_point','coordinate_axis','coordinate_plane']),
        (tr('検査'),['native_measure','measure','interference','section_analysis','cross_sections','edge_comb','surface_curvature','draft_analysis','check_geometry'],['native_measure']),
        (tr('挿入'),['insert','insert_native'],['insert']),
        (tr('アセンブリ','Assemble'),['component','duplicate_component','ground_component',None,'rigid_joint','revolute_joint','slider_joint','cylindrical_joint','ball_joint','motion_link','linear_motion_link','release_joint'],['component']),
        (tr('選択'),['select','box_select','select_all','visible_solids','visible_meshes','invert_visible','fit_selection',None,'edit_sketch'],['select'])])
    page(tr('スケッチ'),[
          (tr('作成'),['line','midpoint_line','polyline',(tr('長方形'),['draw_rectangle','center_rectangle','rounded_rectangle']),(tr('円'),['circle','circle3']),(tr('円弧'),['arc3','arc']),(tr('スプライン'),['spline','control_spline','conic_curve','spline_insert_knot','spline_increase_degree','spline_decrease_degree',None,'spline_comb','spline_control_polygon']),'polygon','circumscribed_polygon','text_sketch',(tr('楕円'),['ellipse','elliptical_arc','ellipse_dimensions',None,'ellipse_resize','ellipse_center']),(tr('スロット'),['slot','arc_slot']),'point',None,
                      'sketch_mirror',(tr('パターン'),['sketch_rectangular_pattern','sketch_rotate']),None,
                      (tr('投影 / 含める','Project / Include'),['project','sketch_intersection']),None,'dimension',
                      (tr('寸法の種類','Dimension Types'),['dimension_length','dimension_horizontal','dimension_vertical','dimension_radius','dimension_diameter','dimension_angle',None,'reference_dimension'])],['line','draw_rectangle','spline','polygon','dimension','arc3']),
          (tr('修正'),['ellipse_resize','ellipse_center',None,'sketch_fillet','sketch_chamfer','trim','extend','sketch_split','sketch_offset',None,'sketch_move','sketch_copy','sketch_rotate','sketch_scale',None,'construction'],['sketch_fillet','trim','sketch_offset']),
          (tr('拘束'),['horizontal','vertical','coincident','point_on_object','tangent','equal','parallel','perpendicular','fix','symmetric',None,'reference_dimension'],
           ['horizontal','vertical','tangent','equal','parallel','perpendicular','fix','symmetric']),
          (tr('検査'),['measure','validate_sketch'],['measure']),
          (tr('選択'),['select_sketch'],['select_sketch']),
          (tr('スケッチを終了'),['finish_sketch'],['finish_sketch'])],compact=True)
    page(tr('ユーティリティ'),[(tr('ナビゲーション'),['fit','fit_selection','look_at_face','top','front','right'],['fit','top','front','right']),
          (tr('表示設定'),['grid','grid_settings','axes','bottom_tabs','appearance','named_views'],['grid','axes']),(tr('検査'),['native_measure','measure','interference','section_analysis','cross_sections','edge_comb','surface_curvature','draft_analysis','check_geometry'],['native_measure'])])
    page(tr('メッシュ'),[(tr('挿入'),['insert','insert_native'],['insert']),
         (tr('作成'),['mesh_tessellate'],['mesh_tessellate']),
         (tr('修正'),['move','move_numeric','mesh_translate','mesh_rotate','mesh_scale',None,'mesh_delete','mesh_components','mesh_refine','mesh_reduce','mesh_smooth','mesh_reverse','mesh_harmonize','mesh_fill','mesh_merge','mesh_convert','mesh_section','mesh_separate','mesh_cut',None,'appearance'],['mesh_delete','mesh_components','mesh_refine','move','mesh_rotate','mesh_scale','mesh_separate','mesh_cut']),
         (tr('検査'),['mesh_inspect','measure'],['mesh_inspect','measure']),
         (tr('出力','Export'),['export'],['export']),
         (tr('選択'),['select','box_select','select_all','visible_solids','visible_meshes','invert_visible','fit_selection'],['select'])])
    page(tr('サーフェス'),[
        (tr('スケッチ'),['sketch','sketch_plane','rectangle'],['sketch']),
        (tr('作成'),['surface_extrude','surface_revolve','surface_sweep','surface_loft','ruled_strip',None,'surface_patch','surface_boundary','surface_sections'],['surface_extrude','surface_revolve','surface_sweep','surface_loft','surface_patch']),
        (tr('修正'),['surface_copy','natural_untrim','surface_untrim','surface_unstitch','surface_projection','surface_isocurve','surface_trim','reverse_normal','surface_stitch','surface_offset','surface_thicken','surface_extend','refine_shape',None,'solid_scale','appearance'],['surface_offset','surface_thicken','surface_extend']),
        (tr('構築'),['offset_plane','midplane','angled_plane','tangent_plane','offset_point_plane','tangent_point_plane','perpendicular_point_plane','three_point_plane','two_edge_plane','path_plane'],['offset_plane']),
        (tr('検査'),['native_measure','measure','interference','section_analysis','cross_sections','edge_comb','surface_curvature','draft_analysis','check_geometry'],['native_measure','section_analysis']),
        (tr('挿入'),['insert','insert_native','export'],['insert']),
        (tr('選択'),['select','box_select','select_all','visible_solids','visible_meshes','invert_visible','fit_selection'],['select'])])
    page(tr('図面','Drawing'),[
        (tr('用紙','Sheet'),['drawing_new','drawing_open','drawing_sheet'],['drawing_new']),
        (tr('作成','Create'),['drawing_view','drawing_projection','drawing_section','drawing_detail'],['drawing_view','drawing_projection','drawing_section','drawing_detail']),
        (tr('寸法','Dimensions'),['drawing_length','drawing_horizontal','drawing_vertical','drawing_radius','drawing_diameter','drawing_angle'],['drawing_length','drawing_diameter','drawing_angle']),
        (tr('注記','Annotations'),['drawing_note','drawing_balloon','drawing_leader','drawing_weld',None,'drawing_circle_center','drawing_edge_center','drawing_face_center','drawing_hatch'],['drawing_note','drawing_circle_center']),
        (tr('修正','Modify'),['drawing_edit','drawing_display','drawing_frames','drawing_erase'],['drawing_edit']),
        (tr('出力','Export'),['drawing_pdf','drawing_svg'],['drawing_pdf']),
        (tr('デザイン','Design'),['drawing_design'],['drawing_design'])])
    import independent_sheetmetal_ui as independent_sheet_ui
    for key,ja,en,kind,icon in [
        ('independent_sheet_base','独自ベース板…','Independent base plate…','Base','sheet-base'),
        ('independent_sheet_bend','曲げ・フランジ…','Bend / flange…','Bend','sheet-flange'),
        ('independent_sheet_holes','独自ベース穴…','Independent base holes…','PerforatedBase','sheet-base'),
        ('independent_sheet_tray','独自複数側面…','Independent multiple sides…','Tray','sheet-flange'),
        ('independent_sheet_flat','独自展開','Independent development','Flat','sheet-unfold')]:
        action(key,tr(ja,en),icon,lambda k=kind:independent_sheet_ui.show(ws,k))
    action('independent_sheet_hem',tr('ヘム（折返し）…','Hem…'),'sheet-flange',
           lambda:independent_sheet_ui.show(ws,'Bend',bend_mode='hem'))
    action('independent_sheet_sketch_bend',tr('スケッチ線に沿って折曲げ…','Bend along sketch line…'),'sheet-flange',
           lambda:independent_sheet_ui.show(ws,'Bend',bend_mode='sketch'))
    action('independent_sheet_sketch',tr('曲げ線付き展開スケッチ','Developed sketch with bend lines'),'sheet-unfold',lambda:independent_sheet_ui.unfold_sketch(ws))
    action('independent_sheet_refresh',tr('独自展開を一括更新','Refresh all independent developments'),'sheet-unfold',lambda:independent_sheet_ui.refresh_flats(ws))
    action('independent_sheet_dxf',tr('独自展開DXF…','Independent developed DXF…'),'export',lambda:independent_sheet_ui.export(ws))
    action('independent_sheet_table',tr('独自曲げ表CSV…','Independent bend table CSV…'),'export',lambda:independent_sheet_ui.export_table(ws))
    page(tr('シートメタル'),[
        (tr('スケッチ'),['sketch','sketch_plane','rectangle','edit_sketch'],['sketch']),
        (tr('作成'),['independent_sheet_base','independent_sheet_bend','independent_sheet_hem','independent_sheet_sketch_bend','independent_sheet_holes','independent_sheet_tray'],['independent_sheet_base','independent_sheet_bend','independent_sheet_holes','independent_sheet_tray']),
        (tr('展開'),['independent_sheet_flat','independent_sheet_sketch','independent_sheet_refresh'],['independent_sheet_flat']),
        (tr('検査'),['native_measure','check_geometry'],['native_measure']),
        (tr('出力','Export'),['independent_sheet_dxf','independent_sheet_table'],['independent_sheet_dxf'])])
    page(tr('プラスチック'),[
        (tr('スケッチ'),['sketch','rectangle','alternating_polygon','edit_sketch'],['sketch']),
        (tr('作成'),['plastic_rib', 'plastic_gusset', 'plastic_boss', 'plastic_snap', 'extrude'],['plastic_rib', 'plastic_gusset', 'plastic_boss', 'plastic_snap']),
        (tr('修正'),['shell','fillet','chamfer','face_offset','delete_faces','solid_draft','angle_chamfer','parameters'],['shell','fillet']),
        (tr('検査'),['native_measure','measure','interference','check_geometry'],['native_measure','interference']),
        (tr('出力','Export'),['export'],['export'])])
    build_manage_page(ws,page,tr)
    ws.ribbon_tabs.currentChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda i: select_ribbon_page(ws,i),(1, 1, False, False)))
    root.setStyleSheet(STYLE)
    root.setSizePolicy(W.QSizePolicy.Ignored,W.QSizePolicy.Fixed)
    ws.toolbar.addWidget(root)
    ws.toolbar.setStyleSheet('QToolBar#FluxCADToolbar {padding:0;margin:0;spacing:0;border:0;border-bottom:1px solid #c9cccf;}')


def build_manage_page(ws, page, tr):
    ws.manage_page_index = ws.ribbon_stack.count()
    page(tr('管理','Manage'), [
        (tr('文書','Document'), ['new','open','examples','example_guide','save','save_as'], ['new','open','save']),
        (tr('パラメータ','Parameters'), ['parameters'], ['parameters']),
        (tr('加工','Manufacturing'), ['cam_setup','cam_profile','cam_pocket','cam_drill','cam_face','cam_sim','cam_post'], ['cam_setup','cam_profile','cam_pocket','cam_drill','cam_face','cam_sim','cam_post']),
        (tr('部品','Components'), ['component','duplicate_component','ground_component','bom'], ['component','duplicate_component','bom']),
        (tr('検査','Inspect'), ['check_geometry','interference'], ['check_geometry','interference']),
        (tr('出力','Export'), ['export'], ['export'])
    ])
    ws.ribbon_tabs.setTabEnabled(ws.tab_indices['manage'], True)
    ws.ribbon_tabs.setTabToolTip(ws.tab_indices['manage'], tr('文書・パラメータ・部品・検査・出力を管理します。','Manage documents, parameters, components, inspection and export.'))
    return ws.manage_page_index

def select_ribbon_page(ws, index):
    mapping = {ws.tab_indices['solid']:0, ws.tab_indices['sketch']:1, ws.tab_indices['utilities']:2, ws.tab_indices['mesh']:3, ws.tab_indices['surface']:4, ws.tab_indices['drawing']:5, ws.tab_indices['sheet']:6, ws.tab_indices['plastic']:7, ws.tab_indices['manage']:ws.manage_page_index}
    ws.ribbon_stack.setCurrentIndex(mapping.get(index,0))


def build_workspace_menu(ws, workspace_menu, tr):
    import drawing
    options = [(tr('デザイン'), 'design'), (tr('レンダリング', 'Rendering'), 'render'),
               (tr('アニメーション', 'Animation'), 'animation'), (tr('シミュレーション'), 'simulation'),
               (tr('製造'), 'manufacture'), (tr('図面'), 'drawing')]
    for title, key in options:
        option = workspace_menu.addAction(title)
        option.setEnabled(key in ('design', 'render', 'animation', 'drawing'))
        option.setObjectName('FluxWorkspace_' + key)
        if key == 'render':
            def open_render():
                import render_tools
                render_tools.show(ws)
            option.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False: ws.safe(open_render),(1, 0, False, False)))
        elif key in ('design', 'drawing'):
            option.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False, draw=key == 'drawing': ws.safe(__import__('builtins')._fullarc_qt_slot(lambda d=draw: drawing.switch(ws, d),(1, 0, False, False))),(2, 0, False, False)))
        elif key == 'animation':
            def open_animation():
                import animation_tools
                animation_tools.show(ws)
            option.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda checked=False: ws.safe(open_animation),(1, 0, False, False)))


def add_save_as(action, command, ws):
    action('save_as', tr('名前を付けて保存…', 'Save As…'), 'document-save-as', __import__('builtins')._fullarc_qt_slot(lambda:__import__('save_guard').save(ws,True),(0, 0, False, False)))


def fit_selection(ws):
    """Frame selected objects with the verified native camera command."""
    doc = App.ActiveDocument
    selected = Gui.Selection.getSelection()
    if not doc or not selected or any(obj.Document != doc for obj in selected):
        raise ValueError(tr('現在の文書の形状を選択してください。', 'Select geometry in the current document.'))
    view = Gui.activeDocument().activeView()
    orientation = view.getCameraOrientation()
    Gui.runCommand('Std_ViewFitSelection')
    view.setCameraOrientation(orientation.Q)
    ws.grid.update()


def select_visible(ws, kind):
    import export_tools
    import model_mesh
    if kind not in ('solid', 'mesh'):
        raise ValueError('Unknown selection kind')
    doc = App.ActiveDocument
    if not doc or ws.current_sketch():
        raise ValueError(tr('スケッチ編集を終了し、文書を開いてください。', 'Finish sketch editing and open a document.'))
    objects = [obj for obj in export_tools.visible_objects(doc)
               if (model_mesh.is_mesh(obj) if kind == 'mesh' else hasattr(obj, 'Shape') and bool(obj.Shape.Solids))]
    if not objects:
        raise ValueError(tr('表示中のメッシュがありません。', 'No visible meshes.') if kind == 'mesh'
                         else tr('表示中のソリッドがありません。', 'No visible solids.'))
    Gui.Selection.clearSelection()
    for obj in objects:
        Gui.Selection.addSelection(obj)
    ws.main.statusBar().showMessage(tr('%d個を選択しました。', 'Selected %d objects.') % len(objects), 5000)
    return objects


def invert_visible(ws):
    import export_tools
    import model_mesh
    from browser import body_owner
    doc=App.ActiveDocument
    if not doc or ws.current_sketch():
        raise ValueError(tr('スケッチ編集を終了し、文書を開いてください。','Finish sketch editing and open a document.'))
    objects=[obj for obj in export_tools.visible_objects(doc)
             if model_mesh.is_mesh(obj) or (hasattr(obj,'Shape') and bool(obj.Shape.Solids))]
    if not objects:
        raise ValueError(tr('表示中のソリッドまたはメッシュがありません。','No visible solids or meshes.'))
    selected={body_owner(obj).Name for obj in Gui.Selection.getSelection() if obj.Document==doc}
    result=[obj for obj in objects if obj.Name not in selected]
    Gui.Selection.clearSelection()
    for obj in result:Gui.Selection.addSelection(obj)
    ws.main.statusBar().showMessage(tr('%d個を選択しました。','Selected %d objects.')%len(result),5000)
    return result


def insert_native_document(ws):
    import model
    doc = App.ActiveDocument
    if not doc or ws.current_sketch() or Gui.Control.activeDialog():
        raise ValueError(tr('文書を開き、編集中の操作を終了してください。','Open a document and finish the active edit.'))
    if any(getattr(panel, 'active', False) for panel in vars(ws).values()):
        raise ValueError(tr('編集中の操作を終了してください。','Finish the active operation.'))
    name = doc.Name
    filename, _ = W.QFileDialog.getOpenFileName(ws.main, tr('FluxCAD部品を挿入','Insert FluxCAD Part'), '', 'FullArcCAD / FreeCAD (*.FCStd)')
    if not filename:
        return []
    if App.ActiveDocument is not doc or App.getDocument(name) is not doc or ws.current_sketch() or Gui.Control.activeDialog():
        raise ValueError(tr('挿入先が変更されました。やり直してください。','The destination changed. Try again.'))
    if any(getattr(panel, 'active', False) for panel in vars(ws).values()):
        raise ValueError(tr('編集中の操作を終了してください。','Finish the active operation.'))
    if not os.path.isfile(filename) or os.path.splitext(filename)[1].lower() != '.fcstd':
        raise ValueError(tr('FCStdファイルを選択してください。','Choose an FCStd file.'))
    if doc.FileName and os.path.normcase(os.path.realpath(doc.FileName)) == os.path.normcase(os.path.realpath(filename)):
        raise ValueError(tr('現在の文書自身は挿入できません。','Cannot insert the current document into itself.'))
    before = {obj.Name for obj in doc.Objects}
    with model.transaction(doc, tr('FluxCAD部品を挿入','Insert FluxCAD Part')):
        doc.mergeProject(filename)
        doc.recompute()
        added = [obj for obj in doc.Objects if obj.Name not in before]
        if not added:
            raise ValueError(tr('挿入するオブジェクトがありません。','No objects to insert.'))
    ws.refresh()
    return added
