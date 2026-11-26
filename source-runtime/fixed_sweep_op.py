import FreeCAD as App,Part
import model
from model_guided_sweep import wire,sampled
from four_ops_values import direction
TITLE=('断面姿勢固定スイープ','Fixed Orientation Sweep')
HINT=('閉じた平面断面→単一開辺の経路を全体選択。断面姿勢を固定して新規ソリッドを作成。\n経路は断面法線方向へ単調に進むこと。回転・尺度・複数辺・形状プレビューなし。','Select whole closed planar profile then one open edge path. Fixed profile orientation,new solid.\nPath must progress monotonically along profile normal. No rotation,scaling,chains or geometry preview.')
DEFAULTS={};FIELDS=[];FLAGS=[]
def selection(s):
    if len(s)!=2 or any(x.SubElementNames for x in s):raise ValueError('Select whole profile then path')
    return [x.Object for x in s],[]
def shape(s,e,o):
    if len(s)!=2 or e or o:raise ValueError('Fixed sweep needs exactly profile and path')
    profile=wire(s[0],True);spine=wire(s[1]);edge=spine.Edges[0];face=Part.Face(profile);normal=App.Vector(*direction(tuple(face.normalAt(0,0))));start,t=sampled(edge,0)
    if face.distToShape(Part.Vertex(start))[0]>1e-6:raise ValueError('Start path inside profile')
    sign=1 if normal.dot(t)>0 else -1
    for i in range(65):
        pt,t=sampled(edge,i/64)
        if sign*normal.dot(t)<1e-7:raise ValueError('Path must advance along profile normal;no perpendicular or reversing tangent')
    mk=Part.BRepOffsetAPI.MakePipeShell(spine);mk.setTolerance(1e-7,1e-7,1e-7);mk.setTrihedronMode(start,normal);mk.add(profile,False,False);mk.build()
    if not mk.makeSolid():raise ValueError('Cannot solidify fixed sweep')
    return mk.shape()
